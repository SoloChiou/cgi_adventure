import axios from "axios";
import { api, setApiToken, setCsrfToken } from "./client";

export interface AuthSession { authenticated: boolean; user: { id: number; username: string } | null; csrf_token?: string; api_token?: string }
export interface PlayerTraits { strength: number; intellect: number; piety: number; vitality: number; dexterity: number; speed: number; charisma: number }
export interface Player { id: number; name: string; level: number; exp: number; next_level_exp: number | null; gold: number; hp: number; mp: number; max_hp: number; max_mp: number; atk: number; defense: number; intelligence: number; magic_defense: number; agility: number; critical: number; traits: PlayerTraits; job_count: number; job: { id: number; name: string; name_en: string; tier: number }; title: { name: string; name_en: string; rank: number; min_level: number; max_level: number } | null; equipment: { weapon: { id: number; name: string } | null; armor: { id: number; name: string } | null; accessory: { id: number; name: string } | null }; skills: { id: number; name: string; name_en: string; mp_cost: number }[] }
export interface Area { id: number; name: string; description: string; required_level: number; cooldown_seconds: number; is_level_simulation: boolean }
export interface DevelopmentJob { id: number; name: string; name_en: string; tier: number }
export interface CreationJob { id: number; name: string; name_en: string; requirements: PlayerTraits }
export interface GameState { player: Player | null; areas: Area[]; recent_battles: { id: number; result: string; monster_name: string }[]; job_transition_available: boolean; development_controls: boolean; development_jobs: DevelopmentJob[]; creation_jobs: CreationJob[] }
export interface BattleResult { battle_id: number; result: string; monster_snapshot: { name: string }; rounds: { round: number; events: Record<string, unknown>[] }[]; rewards: { exp: number; gold: number; drops: { name: string; quantity: number }[]; level_ups: number[] } }

function remember(session: AuthSession) { if (session.csrf_token) setCsrfToken(session.csrf_token); if (session.api_token) setApiToken(session.api_token); return session; }
export async function getSession() { try { return remember((await api.get<AuthSession>("/auth/session/")).data); } catch (error) { if (!axios.isAxiosError(error) || error.response?.status !== 401) throw error; setApiToken(""); return remember((await api.get<AuthSession>("/auth/session/")).data); } }
export async function lineLogin(idToken: string, channelContext: "mini_app" | "web") { return remember((await api.post<AuthSession>("/auth/line/", { id_token: idToken, channel_context: channelContext })).data); }
export async function devLogin() { return remember((await api.post<AuthSession>("/auth/dev/")).data); }
export async function signOut() { await api.post("/auth/logout/"); setApiToken(""); setCsrfToken(""); }
export async function getGame() { return (await api.get<GameState>("/game/")).data; }
export async function createPlayer(name: string, traits: PlayerTraits, jobId: number) { return (await api.post<Player>("/players/", { name, traits, job_id: jobId })).data; }
export async function fight(areaId: number) { return (await api.post<BattleResult>(`/areas/${areaId}/battle/`)).data; }
export async function getInventory() { return (await api.get("/inventory/")).data; }
export async function equip(itemId: number) { return (await api.post(`/inventory/${itemId}/equip/`)).data; }
export async function getLeaderboard() { return (await api.get("/leaderboard/")).data; }
export async function getJobs() { return (await api.get("/jobs/progression/")).data; }
export async function transitionJob(jobId: number) { return (await api.post("/jobs/transition/", { job_id: jobId })).data; }
export async function setDevelopmentPlayer(level: number, jobId: number, hp: number, traits: PlayerTraits) {
  return (await api.patch<Player>("/development/player/", { level, job_id: jobId, hp, traits })).data;
}
