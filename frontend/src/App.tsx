import { FormEvent, useCallback, useEffect, useState } from "react";
import { createPlayer, devLogin, equip, fight, getGame, getInventory, getJobs, getLeaderboard, getSession, lineLogin, setDevelopmentPlayer, signOut, transitionJob, type BattleResult, type GameState, type JobProgression, type PlayerTraits } from "./api/game";
import { contentText, errorMessage, type Locale } from "./localization";
import { getLineLogin, logoutLine } from "./services/line";

type Page = "game" | "inventory" | "leaderboard" | "battle";
const traitFields = ["strength", "intellect", "piety", "vitality", "dexterity", "speed", "charisma"] as const;
const initialTraits: PlayerTraits = { strength: 12, intellect: 8, piety: 8, vitality: 16, dexterity: 9, speed: 8, charisma: 8 };

const copy = {
  en: {
    connecting: "Connecting to the Netherworld Station…", loginRequired: "LINE Login is required to enter the game.", retry: "Try again",
    eyebrow: "Supernatural text RPG", logout: "Log out", switchLanguage: "Traditional Chinese", switchLanguageLabel: "Switch language to Traditional Chinese",
    game: "Adventure", inventory: "Inventory", leaderboard: "Leaderboard", createPlayer: "Create a Wanderer", characterName: "Character name", begin: "Begin adventure",
    newJobPath: "Sense a new career path", chooseJob: "Choose a new job", jobResetNotice: "Changing jobs resets Level to 1, EXP to 0, and all traits to the new job's starting values.", chooseArea: "Choose an area", recommendedLevel: "Recommended level", battle: "Battle",
    encountered: "Encountered", equip: "Equip", emptyInventory: "Your inventory is empty.", wandererRanking: "Wanderer Ranking",
    connectionFailed: "Unable to connect to the service. Please try again later.", idTokenMissing: "LINE Login completed, but no ID token was returned.", edit: "Edit", cancel: "Cancel", level: "Level", job: "Job", title: "Title", hp: "HP", save: "Save", maxLevel: "MAX",
    characterProfile: "Character Profile", characterImage: "Character image placeholder", identity: "Identity", resources: "Resources", traits: "Traits", combatStats: "Combat Stats", equipment: "Equipment", name: "Name", gold: "Gold", weapon: "Weapon", armor: "Armor", accessory: "Accessory", none: "None",
    maxHp: "Max HP", maxMp: "Max MP", attack: "Attack", defense: "Defense", intelligence: "Intelligence", magicDefense: "Magic Defense", agility: "Agility", critical: "Critical",
    strength: "Strength", intellect: "Intellect", piety: "Piety", vitality: "Vitality", dexterity: "Dexterity", speed: "Speed", charisma: "Charisma",
    bonusPointsRemaining: "Bonus points remaining", chooseInitialJob: "Choose a job", noEligibleJobs: "No job matches the current traits.",
    recentBattles: "Recent Battles", noBattles: "No battle records yet.", win: "Victory", lose: "Defeat", townFacilities: "Town Facilities", townOutskirts: "Town Outskirts", enter: "Enter",
    inn: "Traveler's Inn", weaponShop: "Weapon Shop", armorShop: "Armor Shop", trainingHall: "Training Hall", spiritBank: "Spirit Bank", jobShrine: "Job Shrine", adventureExploration: "Adventure Exploration", monsterForest: "Monster Forest", otherworldGate: "Otherworld Gate", arena: "Arena", messageBoard: "Message Board",
    restAndRecover: "Rest and recover.", browseWeapons: "Browse available weapons.", browseArmor: "Browse available armor.", trainAbilities: "Train character abilities.", manageSavings: "Manage stored gold.", advanceYourPath: "Changing jobs resets Level to 1, EXP to 0, and all seven traits to the new job's starting values.", beginExploration: "Set out on an adventure.", exploreTheWilds: "A fearsome forest where powerful monsters slumber.", crossIntoAnotherRealm: "Take turns challenging other players. EXP and gold cannot be earned.", challengeOtherTravelers: "Battle against all players.", readTownNotices: "Send messages to other players.",
    creditsPrefix: "Architecture inspired by FF Adventure by", creditsSuffix: "CGI Adventure is an independent reimplementation.", source: "Source",
    battleResult: "Battle Result", player: "Player", monster: "Monster", round: "Round", attackAction: "Attack", skillAction: "Skill", hit: "Hit", miss: "Miss", criticalHit: "Critical", used: "used", attacked: "attacked", butMissed: "but the attack missed", damage: "damage", hpChange: "HP", mpAfter: "MP after action", rewards: "Rewards", drops: "Drops", noDrops: "No drops", proficiency: "Weapon proficiency", levelUp: "Level up", finalStatus: "Post-battle status",
    allJobRequirements: "All Jobs and Requirements", currentTraits: "Current traits", eligible: "Eligible", unmet: "Unmet", currentJob: "Current", backToTown: "Return to town", battleInProgress: "The battle is being resolved…",
  },
  "zh-TW": {
    connecting: "正在連接幽冥驛站……", loginRequired: "需要 LINE 登入才能進入遊戲。", retry: "重新嘗試",
    eyebrow: "志怪文字 RPG", logout: "登出", switchLanguage: "English", switchLanguageLabel: "切換語言為英文",
    game: "遊歷", inventory: "背包", leaderboard: "榜單", createPlayer: "建立遊方客", characterName: "角色名稱", begin: "踏入江湖",
    newJobPath: "感應新的職業道路", chooseJob: "選擇轉職", jobResetNotice: "轉職後等級重設為 Lv.1、EXP 重設為 0，七種特性改為新職業初始值。", chooseArea: "選擇地區", recommendedLevel: "建議等級", battle: "戰鬥",
    encountered: "遭遇", equip: "裝備", emptyInventory: "背包目前是空的。", wandererRanking: "遊方榜",
    connectionFailed: "無法連接服務，請稍後再試。", idTokenMissing: "LINE 登入完成，但未取得 ID token", edit: "編輯", cancel: "取消", level: "等級", job: "職業", title: "稱號", hp: "HP", save: "儲存", maxLevel: "已達最高等級",
    characterProfile: "角色資料", characterImage: "角色圖片預留位置", identity: "身分", resources: "資源", traits: "七種特性", combatStats: "戰鬥能力", equipment: "裝備", name: "名稱", gold: "金錢", weapon: "武器", armor: "防具", accessory: "飾品", none: "無",
    maxHp: "最大 HP", maxMp: "最大 MP", attack: "攻擊", defense: "防禦", intelligence: "術力", magicDefense: "術防", agility: "敏捷", critical: "暴擊",
    strength: "膂力", intellect: "悟性", piety: "信念", vitality: "根骨", dexterity: "巧手", speed: "身法", charisma: "氣度",
    bonusPointsRemaining: "剩餘特性點數", chooseInitialJob: "選擇職業", noEligibleJobs: "目前特性沒有符合的職業。",
    recentBattles: "近期戰鬥", noBattles: "尚無戰鬥紀錄。", win: "勝利", lose: "敗北", townFacilities: "城鎮設施", townOutskirts: "城鎮郊外", enter: "進入",
    inn: "旅之宿", weaponShop: "武器屋", armorShop: "防具屋", trainingHall: "修行所", spiritBank: "陰司錢莊", jobShrine: "轉職神殿", adventureExploration: "冒險探索", monsterForest: "魔之森林", otherworldGate: "異次元之門", arena: "比武大會", messageBoard: "傳信屋",
    restAndRecover: "休息並恢復狀態。", browseWeapons: "查看可購買的武器。", browseArmor: "查看可購買的防具。", trainAbilities: "修行角色能力。", manageSavings: "管理存放的金錢。", advanceYourPath: "轉職後等級重設為 Lv.1、EXP 重設為 0，七種特性改為新職業初始值。", beginExploration: "展開冒險之旅。", exploreTheWilds: "沉睡著強大魔物的駭人森林。", crossIntoAnotherRealm: "輪流挑戰其他玩家。（無法獲得經驗值及金錢）", challengeOtherTravelers: "和所有玩家進行戰鬥。", readTownNotices: "可以傳信給其他玩家。",
    creditsPrefix: "架構參考 FF Adventure，原作者", creditsSuffix: "CGI Adventure 為獨立重新實作。", source: "保存來源",
    battleResult: "戰鬥結果", player: "玩家", monster: "怪物", round: "回合", attackAction: "攻擊", skillAction: "技能", hit: "命中", miss: "閃避", criticalHit: "暴擊", used: "施展", attacked: "攻擊", butMissed: "但未命中", damage: "點傷害", hpChange: "HP", mpAfter: "行動後 MP", rewards: "戰鬥獎勵", drops: "掉落", noDrops: "無掉落物", proficiency: "武器熟練度", levelUp: "升級", finalStatus: "戰後狀態",
    allJobRequirements: "全部職業與門檻", currentTraits: "目前特性", eligible: "符合", unmet: "未符合", currentJob: "目前職業", backToTown: "返回城鎮", battleInProgress: "戰鬥結算中……",
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

function BattleReport({battle, locale, text}: {battle: BattleResult; locale: Locale; text: typeof copy[Locale]}) {
  return <div className="battle_text_report" aria-live="polite">
    {battle.narratives[locale].map((line, index) => <p className={`battle_tone_${line.tone}`} key={`${line.event_type}-${index}`}>{line.text}</p>)}
    <p>EXP +{battle.rewards.exp}</p>
    <p>Gold +{battle.rewards.gold}</p>
    <p>{text.proficiency}: {battle.rewards.proficiency ? `${contentText(battle.rewards.proficiency.weapon_type, locale)} +${battle.rewards.proficiency.exp}` : "—"}</p>
    <p>{text.levelUp}: {battle.rewards.level_ups.length ? battle.rewards.level_ups.map((level) => `Lv.${level}`).join(", ") : "—"}</p>
    {battle.rewards.drops.length ? battle.rewards.drops.map((drop) => <p key={`${drop.item_id}-${drop.name}`}>{text.drops}: 【{contentText(drop.name, locale)}】×{drop.quantity}</p>) : <p>{text.drops}: {text.noDrops}</p>}
    <p className={`battle_outcome battle_outcome_${battle.result}`}>{battle.result === "win" ? text.win : text.lose}</p>
  </div>;
}

function JobRequirementsTable({progression, locale, text}: {progression: JobProgression; locale: Locale; text: typeof copy[Locale]}) {
  return <div className="job_requirements">
    <h3>{text.allJobRequirements}</h3>
    <div className="current_traits"><strong>{text.currentTraits}</strong>{traitFields.map((trait) => <span key={trait}>{text[trait]} {progression.player.traits[trait]}</span>)}</div>
    <div className="job_requirements_scroll">
      <table>
        <thead><tr><th>{text.job}</th>{traitFields.map((trait) => <th key={trait}>{text[trait]}</th>)}<th>{text.eligible}</th></tr></thead>
        <tbody>{progression.all_jobs.map((job) => <tr key={job.id} className={job.eligible ? "eligible" : job.is_current ? "current" : ""}>
          <th>{locale === "en" ? job.name_en : job.name}</th>
          {traitFields.map((trait) => <td key={trait}>{job.requirements[trait] || "—"}</td>)}
          <td>{job.is_current ? text.currentJob : job.eligible ? text.eligible : text.unmet}</td>
        </tr>)}</tbody>
      </table>
    </div>
  </div>;
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
    setPage("battle"); setBattle(null); setBusy(true); setError("");
    try { setBattle(await fight(areaId)); await refresh(); }
    catch (caught) { setError(errorText(caught, locale)); }
    finally { setBusy(false); }
  }

  async function jobs() {
    if (extra?.all_jobs) {
      setExtra(null);
      return;
    }
    try { setExtra(await getJobs()); }
    catch (caught) { setError(errorText(caught, locale)); }
  }

  async function chooseJob(jobId: number) {
    setBusy(true); setError("");
    try { await transitionJob(jobId); setExtra(null); await refresh(); }
    catch (caught) { setError(errorText(caught, locale)); }
    finally { setBusy(false); }
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
    [text.monsterForest, text.exploreTheWilds], [text.otherworldGate, text.crossIntoAnotherRealm],
    [text.arena, text.challengeOtherTravelers],
    [text.messageBoard, text.readTownNotices],
  ];
  const baseTraits: PlayerTraits = { strength: 9, intellect: 8, piety: 8, vitality: 9, dexterity: 9, speed: 8, charisma: 8 };
  const spentCreationPoints = traitFields.reduce((total, trait) => total + creationTraits[trait] - baseTraits[trait], 0);
  const qualifiedCreationJobs = state?.creation_jobs.filter((job) => traitFields.every((trait) => creationTraits[trait] >= job.requirements[trait])) ?? [];
  const jobProgression = page === "game" && extra?.all_jobs ? extra as JobProgression : null;

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
            <h3 className="table_heading">{text.equipment}</h3>
            <div className="equipment_table">
              <div><span>{text.weapon}</span><strong>{contentText(state.player.equipment.weapon?.name ?? text.none, locale)}</strong></div>
              <div><span>{text.armor}</span><strong>{contentText(state.player.equipment.armor?.name ?? text.none, locale)}</strong></div>
              <div><span>{text.accessory}</span><strong>{contentText(state.player.equipment.accessory?.name ?? text.none, locale)}</strong></div>
            </div>
          </div>
          <div className="character_stats">
            <h3 className="table_heading stat_wide">{text.identity}</h3>
            <div className="stat_row stat_wide"><span>{text.name}</span><strong>{state.player.name}</strong></div>
            <div className="stat_row stat_wide"><span>{text.job}</span>{editingPlayer ? <select aria-label={text.job} name="job_id" defaultValue={state.player.job.id}>{state.development_jobs.map((job) => <option key={job.id} value={job.id}>{locale === "en" && job.name_en ? job.name_en : job.name}</option>)}</select> : <strong>{locale === "en" && state.player.job.name_en ? state.player.job.name_en : state.player.job.name}</strong>}</div>
            <div className="stat_row stat_wide"><span>{text.title}</span><strong>{state.player.title ? (locale === "en" ? state.player.title.name_en : state.player.title.name) : "—"}</strong></div>
            <div className="stat_row"><span>{text.level}</span>{editingPlayer ? <input aria-label={text.level} name="level" type="number" min="1" max="99" defaultValue={state.player.level} required/> : <strong>{state.player.level}</strong>}</div>
            <div className="stat_row"><span>EXP</span><strong>{state.player.exp} / {state.player.next_level_exp ?? text.maxLevel}</strong></div>
            <h3 className="table_heading stat_wide">{text.resources}</h3>
            <div className="stat_row"><span>{text.gold}</span><strong>{state.player.gold}</strong></div>
            <div className="stat_row"><span>HP</span>{editingPlayer ? <span className="editable_value"><input aria-label={text.hp} name="hp" type="number" min="0" defaultValue={state.player.hp} required/> / {state.player.max_hp}</span> : <strong>{state.player.hp} / {state.player.max_hp}</strong>}</div>
            <div className="stat_row"><span>MP</span><strong>{state.player.mp} / {state.player.max_mp}</strong></div>
            <div className="stat_row"><span>{text.maxHp}</span><strong>{state.player.max_hp}</strong></div>
            <div className="stat_row"><span>{text.maxMp}</span><strong>{state.player.max_mp}</strong></div>
            <h3 className="table_heading stat_wide">{text.traits}</h3>
            {traitFields.map((trait) => <div className="stat_row" key={trait}><span>{text[trait]}</span>{editingPlayer ? <input aria-label={text[trait]} name={trait} type="number" min="1" max="99" defaultValue={state.player!.traits[trait]} required/> : <strong>{state.player!.traits[trait]}</strong>}</div>)}
            <h3 className="table_heading stat_wide">{text.combatStats}</h3>
            <div className="stat_row"><span>{text.attack}</span><strong>{state.player.atk}</strong></div>
            <div className="stat_row"><span>{text.defense}</span><strong>{state.player.defense}</strong></div>
            <div className="stat_row"><span>{text.intelligence}</span><strong>{state.player.intelligence}</strong></div>
            <div className="stat_row"><span>{text.magicDefense}</span><strong>{state.player.magic_defense}</strong></div>
            <div className="stat_row"><span>{text.agility}</span><strong>{state.player.agility}</strong></div>
            <div className="stat_row"><span>{text.critical}</span><strong>{Math.round(state.player.critical * 100)}%</strong></div>
          </div>
        </form>
      </section>

      <div className="town_column">
        <section><div className="panel_title"><h2>{text.townFacilities}</h2></div><div className="facility_grid">{facilities.map(([name, description]) => <button type="button" className="display_only_button" key={name}><strong>{name}</strong><small>{description}</small></button>)}</div></section>

        <section><div className="panel_title"><h2>{text.townOutskirts}</h2></div>
          <div className="location_row"><div><strong>{text.jobShrine}</strong><p>{text.advanceYourPath}</p></div><button onClick={() => void jobs()}>{text.enter}</button></div>
          {jobProgression && <div className="job_choices"><h3>{text.chooseJob}</h3><p className="muted">{text.jobResetNotice}</p>{jobProgression.jobs.length ? jobProgression.jobs.map((job) => <button disabled={busy} key={job.id} onClick={() => void chooseJob(job.id)}>{locale === "en" && job.name_en ? job.name_en : job.name}</button>) : <p className="muted">{text.noEligibleJobs}</p>}<JobRequirementsTable progression={jobProgression} locale={locale} text={text}/></div>}
          {state.areas.map((area) => <div className="location_row" key={area.id}><div><strong>{contentText(area.name, locale)}</strong><p>{contentText(area.description, locale)}</p><small>{text.recommendedLevel}: {area.required_level}</small></div><button disabled={busy || state.player!.level < area.required_level} onClick={() => void battleArea(area.id)}>{text.enter}</button></div>)}
          {outskirts.map(([name, description]) => <div className="location_row placeholder_location" key={name}><div><strong>{name}</strong><p>{description}</p></div><button type="button" className="display_only_button">{text.enter}</button></div>)}
        </section>

      </div>
    </div>}

    {page === "battle" && <div className="battle_page">
      <button className="quiet" onClick={() => void openPage("game")}>{text.backToTown}</button>
      {busy && !battle && <section className="battle_loading"><p>{text.battleInProgress}</p></section>}
      {battle && <BattleReport battle={battle} locale={locale} text={text}/>}
    </div>}

    {page === "inventory" && <section><h2>{text.inventory}</h2>{extra?.items?.length ? extra.items.map((row: any) => <article key={row.id}><span>{contentText(row.item.name, locale)} × {row.quantity}</span>{row.item.type !== "material" && <button onClick={async () => { await equip(row.id); setExtra(await getInventory()); }}>{text.equip}</button>}</article>) : <p>{text.emptyInventory}</p>}</section>}
    {page === "leaderboard" && <section><h2>{text.wandererRanking}</h2>{extra?.map?.((row: any) => <p key={row.rank}>{row.rank}. {row.name} · {locale === "en" ? row.job.name_en : row.job.name}{row.title ? ` · ${locale === "en" ? row.title.name_en : row.title.name}` : ""} · Lv.{row.level}</p>)}</section>}
    <footer className="credits">{text.creditsPrefix} <a href="http://www.interq.or.jp/sun/cumro/" target="_blank" rel="noreferrer">D.Takamiya (CUMRO)</a>. {text.creditsSuffix} <a href="https://github.com/timomo/ffadventure" target="_blank" rel="noreferrer">{text.source}</a></footer>
  </main>;
}
