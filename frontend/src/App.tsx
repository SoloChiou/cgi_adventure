import { FormEvent, useCallback, useEffect, useState } from "react";
import { createPlayer, devLogin, equip, fight, getGame, getInventory, getJobs, getLeaderboard, getSession, lineLogin, signOut, transitionJob, type BattleResult, type GameState } from "./api/game";
import { getLineLogin, logoutLine } from "./services/line";

type Page = "game" | "inventory" | "leaderboard";
type Locale = "en" | "zh-TW";

const copy = {
  en: {
    connecting: "Connecting to the Netherworld Station…", loginRequired: "LINE Login is required to enter the game.", retry: "Try again",
    eyebrow: "Supernatural text RPG", logout: "Log out", switchLanguage: "中文", switchLanguageLabel: "Switch language to Traditional Chinese",
    game: "Adventure", inventory: "Inventory", leaderboard: "Leaderboard", createPlayer: "Create a Wanderer", characterName: "Character name", begin: "Begin adventure",
    newJobPath: "Sense a new career path", chooseJob: "Choose a new job", chooseArea: "Choose an area", recommendedLevel: "Recommended level", battle: "Battle",
    encountered: "Encountered", dealt: "dealt", damageTo: "damage to", equip: "Equip", emptyInventory: "Your inventory is empty.", wandererRanking: "Wanderer Ranking",
    connectionFailed: "Unable to connect to the service. Please try again later.", idTokenMissing: "LINE Login completed, but no ID token was returned.",
  },
  "zh-TW": {
    connecting: "正在連接幽冥驛站……", loginRequired: "需要 LINE 登入才能進入遊戲。", retry: "重新嘗試",
    eyebrow: "志怪文字 RPG", logout: "登出", switchLanguage: "English", switchLanguageLabel: "切換語言為英文",
    game: "遊歷", inventory: "背包", leaderboard: "榜單", createPlayer: "建立遊方客", characterName: "角色名稱", begin: "踏入江湖",
    newJobPath: "感應新的職業道路", chooseJob: "選擇轉職", chooseArea: "選擇地區", recommendedLevel: "建議等級", battle: "戰鬥",
    encountered: "遭遇", dealt: "對", damageTo: "造成傷害", equip: "裝備", emptyInventory: "背包目前是空的。", wandererRanking: "遊方榜",
    connectionFailed: "無法連接服務，請稍後再試。", idTokenMissing: "LINE 登入完成，但未取得 ID token",
  },
} as const;

function initialLocale(): Locale {
  try { return window.localStorage.getItem("cgi_adventure_locale") === "zh-TW" ? "zh-TW" : "en"; }
  catch { return "en"; }
}

function errorText(error: unknown, locale: Locale) {
  const value = error as { response?: { data?: { detail?: string } } };
  if (value.response?.data?.detail) return value.response.data.detail;
  if (error instanceof Error && error.message === "LINE 登入完成，但未取得 ID token") return copy[locale].idTokenMissing;
  if (error instanceof Error && error.message.startsWith("LINE ")) return error.message;
  if (error instanceof Error && error.message.startsWith("缺少 VITE_")) return error.message;
  return copy[locale].connectionFailed;
}

export default function App() {
  const [locale, setLocale] = useState<Locale>(initialLocale);
  const text = copy[locale];
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
        if (import.meta.env.DEV && !import.meta.env.VITE_LIFF_ID?.trim() && !import.meta.env.VITE_WEB_LIFF_ID?.trim()) session = await devLogin();
        else {
          const line = await getLineLogin();
          session = await lineLogin(line.idToken, line.channelContext);
        }
      }
      setAuthenticated(session.authenticated);
      if (session.authenticated) await refresh();
    } catch (caught) { setError(errorText(caught, locale)); }
    finally { setBusy(false); }
  }, [refresh]);

  useEffect(() => { void authenticate(); }, [authenticate]);
  useEffect(() => {
    document.documentElement.lang = locale;
    try { window.localStorage.setItem("cgi_adventure_locale", locale); } catch { /* 語言仍會套用於目前頁面。 */ }
  }, [locale]);

  async function openPage(next: Page) {
    setPage(next); setBattle(null); setError("");
    try { setExtra(next === "inventory" ? await getInventory() : next === "leaderboard" ? await getLeaderboard() : null); }
    catch (caught) { setError(errorText(caught, locale)); }
  }

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const data = new FormData(event.currentTarget);
    try { await createPlayer(String(data.get("name") || "")); await refresh(); }
    catch (caught) { setError(errorText(caught, locale)); }
  }

  async function battleArea(areaId: number) {
    setBusy(true); setError("");
    try { setBattle(await fight(areaId)); await refresh(); }
    catch (caught) { setError(errorText(caught, locale)); }
    finally { setBusy(false); }
  }

  async function jobs() {
    try { setExtra(await getJobs()); }
    catch (caught) { setError(errorText(caught, locale)); }
  }

  async function chooseJob(jobId: number) {
    try { await transitionJob(jobId); setExtra(null); await refresh(); }
    catch (caught) { setError(errorText(caught, locale)); }
  }

  if (busy && !state) return <main className="center"><p>{text.connecting}</p></main>;
  if (!authenticated) return <main className="center"><h1>CGI Adventure</h1><p className="error">{error || text.loginRequired}</p><button onClick={() => void authenticate()}>{text.retry}</button></main>;

  return <main className="app">
    <header><div><span className="eyebrow">{text.eyebrow}</span><h1>CGI Adventure</h1></div><div className="header_actions"><button className="quiet" aria-label={text.switchLanguageLabel} onClick={() => setLocale(locale === "en" ? "zh-TW" : "en")}>{text.switchLanguage}</button><button className="quiet" onClick={async () => { await signOut(); try { await logoutLine(); } catch { /* Backend 已完成登出，LIFF 未設定時不阻擋。 */ } setAuthenticated(false); }}>{text.logout}</button></div></header>
    <nav><button onClick={() => void openPage("game")}>{text.game}</button><button onClick={() => void openPage("inventory")}>{text.inventory}</button><button onClick={() => void openPage("leaderboard")}>{text.leaderboard}</button></nav>
    {error && <p className="error">{error}</p>}

    {page === "game" && state && !state.player && <section><h2>{text.createPlayer}</h2><form onSubmit={create}><input name="name" maxLength={20} required placeholder={text.characterName}/><button>{text.begin}</button></form></section>}
    {page === "game" && state?.player && <>
      <section className="status"><h2>{state.player.name} · {state.player.job.name}</h2><p>Lv.{state.player.level}　HP {state.player.hp}/{state.player.max_hp}　MP {state.player.mp}/{state.player.max_mp}</p><p>EXP {state.player.exp}　Gold {state.player.gold}</p><p>ATK {state.player.atk}　DEF {state.player.defense}　INT {state.player.intelligence}　AGI {state.player.agility}</p></section>
      {state.job_transition_available && <section><button onClick={() => void jobs()}>{text.newJobPath}</button></section>}
      {extra?.jobs && <section><h2>{text.chooseJob}</h2>{extra.jobs.map((job: any) => <button key={job.id} onClick={() => void chooseJob(job.id)}>{job.name}</button>)}</section>}
      <section><h2>{text.chooseArea}</h2>{state.areas.map((area) => <article key={area.id}><div><strong>{area.name}</strong><p>{area.description}</p><small>{text.recommendedLevel}: {area.required_level}</small></div><button disabled={busy || state.player!.level < area.required_level} onClick={() => void battleArea(area.id)}>{text.battle}</button></article>)}</section>
      {battle && <section><h2>{battle.result === "win" ? "YOU WIN" : "YOU LOSE"}</h2><p>{text.encountered}: {battle.monster_snapshot.name}</p>{battle.rounds.flatMap((round) => round.events).map((event, index) => <p className="battle-line" key={index}>{locale === "en" ? `${index + 1}. ${String(event.actor_name)} ${text.dealt} ${String(event.damage || 0)} ${text.damageTo} ${String(event.target_name)}` : `${index + 1}. ${String(event.actor_name)} ${text.dealt} ${String(event.target_name)} ${text.damageTo} ${String(event.damage || 0)} 點`}</p>)}<p>EXP +{battle.rewards.exp}　Gold +{battle.rewards.gold}</p></section>}
    </>}

    {page === "inventory" && <section><h2>{text.inventory}</h2>{extra?.items?.length ? extra.items.map((row: any) => <article key={row.id}><span>{row.item.name} × {row.quantity}</span>{row.item.type !== "material" && <button onClick={async () => { await equip(row.id); setExtra(await getInventory()); }}>{text.equip}</button>}</article>) : <p>{text.emptyInventory}</p>}</section>}
    {page === "leaderboard" && <section><h2>{text.wandererRanking}</h2>{extra?.map?.((row: any) => <p key={row.rank}>{row.rank}. {row.name} · {row.job} · Lv.{row.level}</p>)}</section>}
  </main>;
}
