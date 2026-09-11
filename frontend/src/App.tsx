import { FormEvent, useCallback, useEffect, useState } from "react";
import { createPlayer, devLogin, equip, fight, getGame, getInventory, getJobs, getLeaderboard, getSession, lineLogin, setDevelopmentPlayer, signOut, transitionJob, type BattleResult, type GameState, type PlayerTraits } from "./api/game";
import { contentText, errorMessage, type Locale } from "./localization";
import { getLineLogin, logoutLine } from "./services/line";

type Page = "game" | "inventory" | "leaderboard";
const traitFields = ["strength", "intellect", "piety", "vitality", "dexterity", "speed", "charisma"] as const;
const initialTraits: PlayerTraits = { strength: 12, intellect: 8, piety: 8, vitality: 16, dexterity: 9, speed: 8, charisma: 8 };

const copy = {
  en: {
    connecting: "Connecting to the Netherworld Station…", loginRequired: "LINE Login is required to enter the game.", retry: "Try again",
    eyebrow: "Supernatural text RPG", logout: "Log out", switchLanguage: "Traditional Chinese", switchLanguageLabel: "Switch language to Traditional Chinese",
    game: "Adventure", inventory: "Inventory", leaderboard: "Leaderboard", createPlayer: "Create a Wanderer", characterName: "Character name", begin: "Begin adventure",
    newJobPath: "Sense a new career path", chooseJob: "Choose a new job", chooseArea: "Choose an area", recommendedLevel: "Recommended level", battle: "Battle",
    encountered: "Encountered", dealt: "dealt", damageTo: "damage to", equip: "Equip", emptyInventory: "Your inventory is empty.", wandererRanking: "Wanderer Ranking",
    connectionFailed: "Unable to connect to the service. Please try again later.", idTokenMissing: "LINE Login completed, but no ID token was returned.", edit: "Edit", cancel: "Cancel", level: "Level", job: "Job", title: "Title", hp: "HP", save: "Save", maxLevel: "MAX",
    characterProfile: "Character Profile", characterImage: "Character image placeholder", name: "Name", gold: "Gold", weapon: "Weapon", armor: "Armor", accessory: "Accessory", none: "None",
    strength: "Strength", intellect: "Intellect", piety: "Piety", vitality: "Vitality", dexterity: "Dexterity", speed: "Speed", charisma: "Charisma",
    bonusPointsRemaining: "Bonus points remaining", chooseInitialJob: "Choose a job", noEligibleJobs: "No job matches the current traits.",
    recentBattles: "Recent Battles", noBattles: "No battle records yet.", win: "Victory", lose: "Defeat", townFacilities: "Town Facilities", townOutskirts: "Town Outskirts", enter: "Enter",
    inn: "Traveler's Inn", weaponShop: "Weapon Shop", armorShop: "Armor Shop", trainingHall: "Training Hall", spiritBank: "Spirit Bank", jobShrine: "Job Shrine", monsterForest: "Monster Forest", otherworldGate: "Otherworld Gate", arena: "Arena", messageBoard: "Message Board",
    restAndRecover: "Rest and recover.", browseWeapons: "Browse available weapons.", browseArmor: "Browse available armor.", trainAbilities: "Train character abilities.", manageSavings: "Manage stored gold.", advanceYourPath: "Advance along your job path.", exploreTheWilds: "Explore a monster-haunted forest.", crossIntoAnotherRealm: "Cross into another realm.", challengeOtherTravelers: "Challenge other travelers.", readTownNotices: "Read notices from other travelers.",
  },
  "zh-TW": {
    connecting: "正在連接幽冥驛站……", loginRequired: "需要 LINE 登入才能進入遊戲。", retry: "重新嘗試",
    eyebrow: "志怪文字 RPG", logout: "登出", switchLanguage: "English", switchLanguageLabel: "切換語言為英文",
    game: "遊歷", inventory: "背包", leaderboard: "榜單", createPlayer: "建立遊方客", characterName: "角色名稱", begin: "踏入江湖",
    newJobPath: "感應新的職業道路", chooseJob: "選擇轉職", chooseArea: "選擇地區", recommendedLevel: "建議等級", battle: "戰鬥",
    encountered: "遭遇", dealt: "對", damageTo: "造成傷害", equip: "裝備", emptyInventory: "背包目前是空的。", wandererRanking: "遊方榜",
    connectionFailed: "無法連接服務，請稍後再試。", idTokenMissing: "LINE 登入完成，但未取得 ID token", edit: "編輯", cancel: "取消", level: "等級", job: "職業", title: "稱號", hp: "HP", save: "儲存", maxLevel: "已達最高等級",
    characterProfile: "角色資料", characterImage: "角色圖片預留位置", name: "名稱", gold: "金錢", weapon: "武器", armor: "防具", accessory: "飾品", none: "無",
    strength: "膂力", intellect: "悟性", piety: "信念", vitality: "根骨", dexterity: "巧手", speed: "身法", charisma: "氣度",
    bonusPointsRemaining: "剩餘特性點數", chooseInitialJob: "選擇職業", noEligibleJobs: "目前特性沒有符合的職業。",
    recentBattles: "近期戰鬥", noBattles: "尚無戰鬥紀錄。", win: "勝利", lose: "敗北", townFacilities: "城鎮設施", townOutskirts: "城鎮郊外", enter: "進入",
    inn: "旅之宿", weaponShop: "武器屋", armorShop: "防具屋", trainingHall: "修行所", spiritBank: "陰司錢莊", jobShrine: "轉職神殿", monsterForest: "魔之森林", otherworldGate: "異次元之門", arena: "比武大會", messageBoard: "傳信屋",
    restAndRecover: "休息並恢復狀態。", browseWeapons: "查看可購買的武器。", browseArmor: "查看可購買的防具。", trainAbilities: "修行角色能力。", manageSavings: "管理存放的金錢。", advanceYourPath: "沿目前道路進行轉職。", exploreTheWilds: "探索妖物出沒的森林。", crossIntoAnotherRealm: "前往另一個異界。", challengeOtherTravelers: "挑戰其他遊方客。", readTownNotices: "閱讀其他遊方客的留言。",
  },
} as const;

function initialLocale(): Locale {
  try { return window.localStorage.getItem("cgi_adventure_locale") === "zh-TW" ? "zh-TW" : "en"; }
  catch { return "en"; }
}

function errorText(error: unknown, locale: Locale) {
  const value = error as { response?: { data?: { detail?: string } } };
  if (value.response?.data?.detail) return errorMessage(value.response.data.detail, locale) || copy[locale].connectionFailed;
  if (error instanceof Error && error.message === "LINE 登入完成，但未取得 ID token") return copy[locale].idTokenMissing;
  if (error instanceof Error && error.message.startsWith("LINE ")) return locale === "en" ? "LINE authentication failed." : error.message;
  if (error instanceof Error && error.message.startsWith("缺少 VITE_")) return locale === "en" ? "A required LINE configuration value is missing." : error.message;
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
  const [editingPlayer, setEditingPlayer] = useState(false);
  const [creationTraits, setCreationTraits] = useState<PlayerTraits>(initialTraits);

  const refresh = useCallback(async () => { setState(await getGame()); }, []);

  const authenticate = useCallback(async () => {
    setBusy(true); setError("");
    try {
      const useDevLogin = import.meta.env.DEV && !import.meta.env.VITE_LIFF_ID?.trim() && !import.meta.env.VITE_WEB_LIFF_ID?.trim();
      let session = useDevLogin ? await devLogin() : await getSession();
      if (!session.authenticated) {
        const line = await getLineLogin();
        session = await lineLogin(line.idToken, line.channelContext);
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
    try { await createPlayer(String(data.get("name") || ""), creationTraits, Number(data.get("job_id"))); await refresh(); }
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

  async function savePlayer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!state?.player) return;
    const data = new FormData(event.currentTarget);
    const level = Number(data.get("level"));
    const jobId = Number(data.get("job_id"));
    const hp = Number(data.get("hp"));
    const traits = {
      strength: Number(data.get("strength")), intellect: Number(data.get("intellect")), piety: Number(data.get("piety")),
      vitality: Number(data.get("vitality")), dexterity: Number(data.get("dexterity")), speed: Number(data.get("speed")), charisma: Number(data.get("charisma")),
    };
    setBusy(true); setError("");
    try { await setDevelopmentPlayer(level, jobId, hp, traits); await refresh(); setEditingPlayer(false); }
    catch (caught) { setError(errorText(caught, locale)); }
    finally { setBusy(false); }
  }

  if (busy && !state) return <main className="center"><p>{text.connecting}</p></main>;
  if (!authenticated) return <main className="center"><h1>CGI Adventure</h1><p className="error">{error || text.loginRequired}</p><button onClick={() => void authenticate()}>{text.retry}</button></main>;

  const facilities = [
    [text.inn, text.restAndRecover], [text.weaponShop, text.browseWeapons], [text.armorShop, text.browseArmor],
    [text.trainingHall, text.trainAbilities], [text.spiritBank, text.manageSavings],
  ];
  const outskirts = [
    [text.jobShrine, text.advanceYourPath], [text.monsterForest, text.exploreTheWilds],
    [text.otherworldGate, text.crossIntoAnotherRealm], [text.arena, text.challengeOtherTravelers],
    [text.messageBoard, text.readTownNotices],
  ];
  const baseTraits: PlayerTraits = { strength: 9, intellect: 8, piety: 8, vitality: 9, dexterity: 9, speed: 8, charisma: 8 };
  const spentCreationPoints = traitFields.reduce((total, trait) => total + creationTraits[trait] - baseTraits[trait], 0);
  const qualifiedCreationJobs = state?.creation_jobs.filter((job) => traitFields.every((trait) => creationTraits[trait] >= job.requirements[trait])) ?? [];

  return <main className="app">
    <header><div><span className="eyebrow">{text.eyebrow}</span><h1>CGI Adventure</h1></div><div className="header_actions"><button className="quiet" aria-label={text.switchLanguageLabel} onClick={() => setLocale(locale === "en" ? "zh-TW" : "en")}>{text.switchLanguage}</button><button className="quiet" onClick={async () => { await signOut(); try { await logoutLine(); } catch { /* Backend 已完成登出，LIFF 未設定時不阻擋。 */ } setAuthenticated(false); }}>{text.logout}</button></div></header>
    <nav><button onClick={() => void openPage("game")}>{text.game}</button><button onClick={() => void openPage("inventory")}>{text.inventory}</button><button onClick={() => void openPage("leaderboard")}>{text.leaderboard}</button></nav>
    {error && <p className="error">{error}</p>}

    {page === "game" && state && !state.player && <section><h2>{text.createPlayer}</h2><form onSubmit={create}><input name="name" maxLength={20} required placeholder={text.characterName}/><div className="creation_traits">{traitFields.map((trait) => <label key={trait}><span>{text[trait]}</span><input aria-label={text[trait]} type="number" min={baseTraits[trait]} max="18" value={creationTraits[trait]} onChange={(event) => setCreationTraits({...creationTraits, [trait]: Number(event.target.value)})}/></label>)}</div><p className={spentCreationPoints === 10 ? "muted" : "error"}>{text.bonusPointsRemaining}: {10 - spentCreationPoints}</p><label><span>{text.chooseInitialJob}</span><select name="job_id" required>{qualifiedCreationJobs.map((job) => <option key={job.id} value={job.id}>{locale === "en" ? job.name_en : job.name}</option>)}</select></label>{!qualifiedCreationJobs.length && <p className="error">{text.noEligibleJobs}</p>}<button disabled={spentCreationPoints !== 10 || !qualifiedCreationJobs.length}>{text.begin}</button></form></section>}
    {page === "game" && state?.player && <div className="game_dashboard">
      <section className="character_panel">
        <div className="panel_title"><h2>{text.characterProfile}</h2>{state.development_controls && !editingPlayer && <button className="quiet compact_button" onClick={() => setEditingPlayer(true)}>{text.edit}</button>}{editingPlayer && <div className="status_actions"><button type="button" className="quiet compact_button" onClick={() => setEditingPlayer(false)}>{text.cancel}</button><button className="compact_button" form="character_editor" disabled={busy}>{text.save}</button></div>}</div>
        <form id="character_editor" className="character_content" onSubmit={savePlayer}>
          <div className="portrait_column">
            <div className="portrait_placeholder" role="img" aria-label={text.characterImage}/>
            <div className="equipment_table">
              <div><span>{text.weapon}</span><strong>{contentText(state.player.equipment.weapon?.name ?? text.none, locale)}</strong></div>
              <div><span>{text.armor}</span><strong>{contentText(state.player.equipment.armor?.name ?? text.none, locale)}</strong></div>
              <div><span>{text.accessory}</span><strong>{contentText(state.player.equipment.accessory?.name ?? text.none, locale)}</strong></div>
            </div>
          </div>
          <div className="character_stats">
            <div className="stat_row stat_wide"><span>{text.name}</span><strong>{state.player.name}</strong></div>
            <div className="stat_row stat_wide"><span>{text.job}</span>{editingPlayer ? <select aria-label={text.job} name="job_id" defaultValue={state.player.job.id}>{state.development_jobs.map((job) => <option key={job.id} value={job.id}>{locale === "en" && job.name_en ? job.name_en : job.name}</option>)}</select> : <strong>{locale === "en" && state.player.job.name_en ? state.player.job.name_en : state.player.job.name}</strong>}</div>
            <div className="stat_row stat_wide"><span>{text.title}</span><strong>{state.player.title ? (locale === "en" ? state.player.title.name_en : state.player.title.name) : "—"}</strong></div>
            <div className="stat_row"><span>{text.level}</span>{editingPlayer ? <input aria-label={text.level} name="level" type="number" min="1" max="99" defaultValue={state.player.level} required/> : <strong>{state.player.level}</strong>}</div>
            <div className="stat_row"><span>EXP</span><strong>{state.player.exp} / {state.player.next_level_exp ?? text.maxLevel}</strong></div>
            <div className="stat_row"><span>{text.gold}</span><strong>{state.player.gold}</strong></div>
            <div className="stat_row"><span>HP</span>{editingPlayer ? <span className="editable_value"><input aria-label={text.hp} name="hp" type="number" min="0" defaultValue={state.player.hp} required/> / {state.player.max_hp}</span> : <strong>{state.player.hp} / {state.player.max_hp}</strong>}</div>
            <div className="stat_row"><span>MP</span><strong>{state.player.mp} / {state.player.max_mp}</strong></div>
            <div className="stat_row"><span>ATK</span><strong>{state.player.atk}</strong></div>
            <div className="stat_row"><span>DEF</span><strong>{state.player.defense}</strong></div>
            <div className="stat_row"><span>INT</span><strong>{state.player.intelligence}</strong></div>
            <div className="stat_row"><span>MDEF</span><strong>{state.player.magic_defense}</strong></div>
            <div className="stat_row"><span>AGI</span><strong>{state.player.agility}</strong></div>
            <div className="stat_row"><span>CRIT</span><strong>{Math.round(state.player.critical * 100)}%</strong></div>
            {traitFields.map((trait) => <div className="stat_row" key={trait}><span>{text[trait]}</span>{editingPlayer ? <input aria-label={text[trait]} name={trait} type="number" min="1" max="99" defaultValue={state.player!.traits[trait]} required/> : <strong>{state.player!.traits[trait]}</strong>}</div>)}
          </div>
        </form>
      </section>

      <div className="town_column">
        <section><div className="panel_title"><h2>{text.recentBattles}</h2></div>{state.recent_battles.length ? <div className="record_table">{state.recent_battles.map((record) => <div key={record.id}><strong>{record.result === "win" ? text.win : text.lose}</strong><span>{contentText(record.monster_name, locale)}</span></div>)}</div> : <p className="muted">{text.noBattles}</p>}</section>

        <section><div className="panel_title"><h2>{text.townFacilities}</h2></div><div className="facility_grid">{facilities.map(([name, description]) => <button type="button" className="display_only_button" key={name}><strong>{name}</strong><small>{description}</small></button>)}</div></section>

        <section><div className="panel_title"><h2>{text.townOutskirts}</h2></div>
          {state.job_transition_available && <div className="location_row"><div><strong>{text.jobShrine}</strong><p>{text.advanceYourPath}</p></div><button onClick={() => void jobs()}>{text.enter}</button></div>}
          {extra?.jobs && <div className="job_choices"><h3>{text.chooseJob}</h3>{extra.jobs.map((job: any) => <button key={job.id} onClick={() => void chooseJob(job.id)}>{locale === "en" && job.name_en ? job.name_en : job.name}</button>)}</div>}
          {state.areas.map((area) => <div className="location_row" key={area.id}><div><strong>{contentText(area.name, locale)}</strong><p>{contentText(area.description, locale)}</p><small>{text.recommendedLevel}: {area.required_level}</small></div><button disabled={busy || state.player!.level < area.required_level} onClick={() => void battleArea(area.id)}>{text.battle}</button></div>)}
          {outskirts.map(([name, description]) => <div className="location_row placeholder_location" key={name}><div><strong>{name}</strong><p>{description}</p></div><button type="button" className="display_only_button">{text.enter}</button></div>)}
        </section>

        {battle && <section><div className="panel_title"><h2>{battle.result === "win" ? "YOU WIN" : "YOU LOSE"}</h2></div><p>{text.encountered}: {contentText(battle.monster_snapshot.name, locale)}</p>{battle.rounds.flatMap((round) => round.events).map((event, index) => { const actor = String(event.actor_unit_id).startsWith("monster:") ? contentText(event.actor_name, locale) : String(event.actor_name); const target = String(event.target_unit_ids).includes("monster:") ? contentText(event.target_name, locale) : String(event.target_name); return <p className="battle-line" key={index}>{locale === "en" ? `${index + 1}. ${actor} ${text.dealt} ${String(event.damage || 0)} ${text.damageTo} ${target}` : `${index + 1}. ${actor} ${text.dealt} ${target} ${text.damageTo} ${String(event.damage || 0)} 點`}</p>; })}<p>EXP +{battle.rewards.exp}　Gold +{battle.rewards.gold}</p></section>}
      </div>
    </div>}

    {page === "inventory" && <section><h2>{text.inventory}</h2>{extra?.items?.length ? extra.items.map((row: any) => <article key={row.id}><span>{contentText(row.item.name, locale)} × {row.quantity}</span>{row.item.type !== "material" && <button onClick={async () => { await equip(row.id); setExtra(await getInventory()); }}>{text.equip}</button>}</article>) : <p>{text.emptyInventory}</p>}</section>}
    {page === "leaderboard" && <section><h2>{text.wandererRanking}</h2>{extra?.map?.((row: any) => <p key={row.rank}>{row.rank}. {row.name} · {locale === "en" ? row.job.name_en : row.job.name}{row.title ? ` · ${locale === "en" ? row.title.name_en : row.title.name}` : ""} · Lv.{row.level}</p>)}</section>}
  </main>;
}
