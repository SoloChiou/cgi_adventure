import axios from "axios";
import { api, setApiToken, setCsrfToken } from "./client";

export interface AuthSession { authenticated: boolean; user: { id: number; username: string } | null; csrf_token?: string; api_token?: string }
export interface Player { id: number; name: string; level: number; exp: number; gold: number; hp: number; mp: number; max_hp: number; max_mp: number; atk: number; defense: number; intelligence: number; magic_defense: number; agility: number; critical: number; job_count: number; job: { id: number; name: string; tier: number }; skills: { id: number; name: string; mp_cost: number }[] }
export interface Area { id: number; name: string; description: string; required_level: number; cooldown_seconds: number; is_level_simulation: boolean }
export interface GameState { player: Player | null; areas: Area[]; recent_battles: { id: number; result: string; monster_name: string }[]; job_transition_available: boolean; development_controls: boolean }
export interface BattleResult { battle_id: number; result: string; monster_snapshot: { name: string }; rounds: { round: number; events: Record<string, unknown>[] }[]; rewards: { exp: number; gold: number; drops: { name: string; quantity: number }[]; level_ups: number[] } }

function remember(session: AuthSession) { if (session.csrf_token) setCsrfToken(session.csrf_token); if (session.api_token) setApiToken(session.api_token); return session; }
export async function getSession() { try { return remember((await api.get<AuthSession>("/auth/session/")).data); } catch (error) { if (!axios.isAxiosError(error) || error.response?.status !== 401) throw error; setApiToken(""); return remember((await api.get<AuthSession>("/auth/session/")).data); } }
export async function lineLogin(idToken: string) { return remember((await api.post<AuthSession>("/auth/line/", { id_token: idToken })).data); }
export async function devLogin() { return remember((await api.post<AuthSession>("/auth/dev/")).data); }
export async function signOut() { await api.post("/auth/logout/"); setApiToken(""); setCsrfToken(""); }
export async function getGame() { return (await api.get<GameState>("/game/")).data; }
export async function createPlayer(name: string) { return (await api.post<Player>("/players/", { name })).data; }
export async function fight(areaId: number) { return (await api.post<BattleResult>(`/areas/${areaId}/battle/`)).data; }
export async function getInventory() { return (await api.get("/inventory/")).data; }
export async function equip(itemId: number) { return (await api.post(`/inventory/${itemId}/equip/`)).data; }
export async function getLeaderboard() { return (await api.get("/leaderboard/")).data; }
export async function getJobs() { return (await api.get("/jobs/progression/")).data; }
export async function transitionJob(jobId: number) { return (await api.post("/jobs/transition/", { job_id: jobId })).data; }
