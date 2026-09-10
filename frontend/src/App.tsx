import { FormEvent, useCallback, useEffect, useState } from "react";
import { createPlayer, devLogin, equip, fight, getGame, getInventory, getJobs, getLeaderboard, getSession, lineLogin, signOut, transitionJob, type BattleResult, type GameState } from "./api/game";
import { getLineIdToken, logoutLine } from "./services/line";

type Page = "game" | "inventory" | "leaderboard";

function errorText(error: unknown) {
  const value = error as { response?: { data?: { detail?: string } } };
  if (value.response?.data?.detail) return value.response.data.detail;
  if (error instanceof Error && error.message.startsWith("LINE ")) return error.message;
  if (error instanceof Error && error.message === "缺少 VITE_LIFF_ID") return error.message;
  return "無法連接服務，請稍後再試。";
}

export default function App() {
  const [authenticated, setAuthenticated] = useState(false);
  const [state, setState] = useState<GameState | null>(null);
  const [page, setPage] = useState<Page>("game");
  const [extra, setExtra] = useState<any>(null);
  const [battle, setBattle] = useState<BattleResult | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => { setState(await getGame()); }, []);

  const authenticate = useCallback(async () => {
    setBusy(true); setError("");
    try {
      let session = await getSession();
      if (!session.authenticated) {
        if (import.meta.env.DEV && !import.meta.env.VITE_LIFF_ID?.trim()) session = await devLogin();
        else session = await lineLogin(await getLineIdToken());
      }
      setAuthenticated(session.authenticated);
      if (session.authenticated) await refresh();
    } catch (caught) { setError(errorText(caught)); }
    finally { setBusy(false); }
  }, [refresh]);

  useEffect(() => { void authenticate(); }, [authenticate]);

  async function openPage(next: Page) {
    setPage(next); setBattle(null); setError("");
    try { setExtra(next === "inventory" ? await getInventory() : next === "leaderboard" ? await getLeaderboard() : null); }
    catch (caught) { setError(errorText(caught)); }
  }

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = new FormData(event.currentTarget);
    try { await createPlayer(String(data.get("name") || "")); await refresh(); }
    catch (caught) { setError(errorText(caught)); }
  }

  async function battleArea(areaId: number) {
    setBusy(true); setError("");
    try { setBattle(await fight(areaId)); await refresh(); }
    catch (caught) { setError(errorText(caught)); }
    finally { setBusy(false); }
  }

  async function jobs() {
    try { setExtra(await getJobs()); }
    catch (caught) { setError(errorText(caught)); }
  }

  async function chooseJob(jobId: number) {
    try { await transitionJob(jobId); setExtra(null); await refresh(); }
    catch (caught) { setError(errorText(caught)); }
  }

  if (busy && !state) return <main className="center"><p>正在連接幽冥驛站……</p></main>;
  if (!authenticated) return <main className="center"><h1>CGI Adventure</h1><p className="error">{error || "需要 LINE 登入才能進入遊戲。"}</p><button onClick={() => void authenticate()}>重新嘗試</button></main>;

  return <main className="app">
    <header><div><span className="eyebrow">志怪文字 RPG</span><h1>CGI Adventure</h1></div><button className="quiet" onClick={async () => { await signOut(); try { await logoutLine(); } catch { /* Backend 已完成登出，LIFF 未設定時不阻擋。 */ } setAuthenticated(false); }}>登出</button></header>
    <nav><button onClick={() => void openPage("game")}>遊歷</button><button onClick={() => void openPage("inventory")}>背包</button><button onClick={() => void openPage("leaderboard")}>榜單</button></nav>
    {error && <p className="error">{error}</p>}

    {page === "game" && state && !state.player && <section><h2>建立遊方客</h2><form onSubmit={create}><input name="name" maxLength={20} required placeholder="角色名稱"/><button>踏入江湖</button></form></section>}
    {page === "game" && state?.player && <>
      <section className="status"><h2>{state.player.name} · {state.player.job.name}</h2><p>Lv.{state.player.level}　HP {state.player.hp}/{state.player.max_hp}　MP {state.player.mp}/{state.player.max_mp}</p><p>EXP {state.player.exp}　Gold {state.player.gold}</p><p>ATK {state.player.atk}　DEF {state.player.defense}　INT {state.player.intelligence}　AGI {state.player.agility}</p></section>
      {state.job_transition_available && <section><button onClick={() => void jobs()}>感應新的職業道路</button></section>}
      {extra?.jobs && <section><h2>選擇轉職</h2>{extra.jobs.map((job: any) => <button key={job.id} onClick={() => void chooseJob(job.id)}>{job.name}</button>)}</section>}
      <section><h2>選擇地區</h2>{state.areas.map((area) => <article key={area.id}><div><strong>{area.name}</strong><p>{area.description}</p><small>建議等級：{area.required_level}</small></div><button disabled={busy || state.player!.level < area.required_level} onClick={() => void battleArea(area.id)}>戰鬥</button></article>)}</section>
      {battle && <section><h2>{battle.result === "win" ? "YOU WIN" : "YOU LOSE"}</h2><p>遭遇：{battle.monster_snapshot.name}</p>{battle.rounds.flatMap((round) => round.events).map((event, index) => <p className="battle-line" key={index}>{index + 1}. {String(event.actor_name)} 對 {String(event.target_name)} 造成 {String(event.damage || 0)} 點傷害</p>)}<p>EXP +{battle.rewards.exp}　Gold +{battle.rewards.gold}</p></section>}
    </>}

    {page === "inventory" && <section><h2>背包</h2>{extra?.items?.length ? extra.items.map((row: any) => <article key={row.id}><span>{row.item.name} × {row.quantity}</span>{row.item.type !== "material" && <button onClick={async () => { await equip(row.id); setExtra(await getInventory()); }}>裝備</button>}</article>) : <p>背包目前是空的。</p>}</section>}
    {page === "leaderboard" && <section><h2>遊方榜</h2>{extra?.map?.((row: any) => <p key={row.rank}>{row.rank}. {row.name} · {row.job} · Lv.{row.level}</p>)}</section>}
  </main>;
}
