import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { AssessmentResult } from "@/types";

export default function IndexPage() {
  const queryClient = useQueryClient();
  const [assessment, setAssessment] = useState<AssessmentResult | null>(null);

  const usersQuery = useQuery({ queryKey: ["users"], queryFn: api.listUsers });
  const substancesQuery = useQuery({ queryKey: ["substances"], queryFn: api.listSubstances });
  const logsQuery = useQuery({ queryKey: ["daily-logs"], queryFn: api.listDailyLogs });
  const healthQuery = useQuery({ queryKey: ["health"], queryFn: api.health });

  const userMutation = useMutation({
    mutationFn: api.createUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });

  const substanceMutation = useMutation({
    mutationFn: api.createSubstance,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["substances"] }),
  });

  const logMutation = useMutation({
    mutationFn: api.createDailyLog,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["daily-logs"] }),
  });

  const assessmentMutation = useMutation({
    mutationFn: api.assess,
    onSuccess: (data) => setAssessment(data),
  });

  const userOptions = usersQuery.data ?? [];
  const substanceOptions = substancesQuery.data ?? [];

  const logRows = useMemo(() => logsQuery.data ?? [], [logsQuery.data]);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-50">
      <div className="mx-auto max-w-7xl p-6 md:p-10 space-y-8">
        <header className="space-y-3">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <h1 className="text-4xl font-bold">Addiction Tracker — V1</h1>
            <div className="rounded-full border border-slate-700 px-4 py-2 text-sm text-slate-200">
              API: {healthQuery.data?.status === "ok" ? "connectée" : "en attente"}
            </div>
          </div>
          <p className="text-slate-300 max-w-3xl">
            Suivi multi-substances avec journal quotidien, notes TCC et routage IA vers
            exercice cognitivo-comportemental ou alerte locale CSAPA.
          </p>
        </header>

        <section className="grid gap-6 lg:grid-cols-2">
          <Card title="Créer un utilisateur">
            <SimpleUserForm
              onSubmit={(payload) => userMutation.mutateAsync(payload)}
              loading={userMutation.isPending}
            />
          </Card>

          <Card title="Créer une substance">
            <SimpleSubstanceForm
              onSubmit={(payload) => substanceMutation.mutateAsync(payload)}
              loading={substanceMutation.isPending}
            />
          </Card>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <Card title="Journal quotidien">
            <DailyLogForm
              users={userOptions}
              substances={substanceOptions}
              onSubmit={(payload) => logMutation.mutateAsync(payload)}
              loading={logMutation.isPending}
            />
          </Card>

          <Card title="Évaluation IA">
            <AssessmentForm
              substances={substanceOptions}
              onSubmit={(payload) => assessmentMutation.mutateAsync(payload)}
              loading={assessmentMutation.isPending}
            />
            {assessment && <AssessmentPanel result={assessment} />}
          </Card>
        </section>

        <section className="grid gap-6 lg:grid-cols-3">
          <Card title={`Utilisateurs (${userOptions.length})`}>
            <ul className="space-y-2 text-sm">
              {userOptions.map((user) => (
                <li key={user.id} className="rounded-lg bg-slate-800/70 p-3">
                  <div className="font-medium">{user.first_name} {user.last_name}</div>
                  <div className="text-slate-400">{user.email}</div>
                </li>
              ))}
            </ul>
          </Card>

          <Card title={`Substances (${substanceOptions.length})`}>
            <ul className="space-y-2 text-sm">
              {substanceOptions.map((substance) => (
                <li key={substance.id} className="rounded-lg bg-slate-800/70 p-3">
                  <div className="font-medium">{substance.name}</div>
                  <div className="text-slate-400">{substance.category} · risque {substance.risk_level}</div>
                </li>
              ))}
            </ul>
          </Card>

          <Card title={`Logs (${logRows.length})`}>
            <div className="space-y-2 text-sm max-h-[420px] overflow-auto pr-1">
              {logRows.map((log) => (
                <div key={log.id} className="rounded-lg bg-slate-800/70 p-3">
                  <div className="font-medium">{log.log_date}</div>
                  <div className="text-slate-300">Craving {log.craving_level}/10 · Mood {log.mood_score ?? "n/a"}</div>
                  {log.cbt_notes ? <div className="text-slate-400 mt-1">TCC: {log.cbt_notes}</div> : null}
                </div>
              ))}
            </div>
          </Card>
        </section>
      </div>
    </main>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/80 p-5 shadow-xl shadow-black/20">
      <h2 className="text-xl font-semibold mb-4">{title}</h2>
      {children}
    </section>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-2 text-sm">
      <span className="text-slate-300">{label}</span>
      {children}
    </label>
  );
}

function inputClassName() {
  return "w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-50 outline-none focus:border-sky-500";
}

function buttonClassName(disabled?: boolean) {
  return `rounded-lg px-4 py-2 font-medium transition ${disabled ? "bg-slate-700 text-slate-400" : "bg-sky-600 hover:bg-sky-500 text-white"}`;
}

function SimpleUserForm({ onSubmit, loading }: { onSubmit: (payload: any) => Promise<unknown>; loading: boolean }) {
  return (
    <form
      className="space-y-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const fd = new FormData(e.currentTarget);
        await onSubmit({
          email: String(fd.get("email") || ""),
          first_name: String(fd.get("first_name") || ""),
          last_name: String(fd.get("last_name") || ""),
          password_hash: null,
        });
        e.currentTarget.reset();
      }}
    >
      <Field label="Prénom"><input name="first_name" className={inputClassName()} required /></Field>
      <Field label="Nom"><input name="last_name" className={inputClassName()} required /></Field>
      <Field label="Email"><input type="email" name="email" className={inputClassName()} required /></Field>
      <button className={buttonClassName(loading)} disabled={loading}>{loading ? "Création..." : "Créer l'utilisateur"}</button>
    </form>
  );
}

function SimpleSubstanceForm({ onSubmit, loading }: { onSubmit: (payload: any) => Promise<unknown>; loading: boolean }) {
  return (
    <form
      className="space-y-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const fd = new FormData(e.currentTarget);
        await onSubmit({
          name: String(fd.get("name") || ""),
          category: String(fd.get("category") || ""),
          description: String(fd.get("description") || ""),
          risk_level: String(fd.get("risk_level") || "moderate"),
        });
        e.currentTarget.reset();
      }}
    >
      <Field label="Nom"><input name="name" className={inputClassName()} required /></Field>
      <Field label="Catégorie"><input name="category" className={inputClassName()} required /></Field>
      <Field label="Niveau de risque">
        <select name="risk_level" className={inputClassName()} defaultValue="moderate">
          <option value="low">low</option>
          <option value="moderate">moderate</option>
          <option value="high">high</option>
        </select>
      </Field>
      <Field label="Description"><textarea name="description" className={inputClassName()} rows={3} /></Field>
      <button className={buttonClassName(loading)} disabled={loading}>{loading ? "Création..." : "Créer la substance"}</button>
    </form>
  );
}

function DailyLogForm({ users, substances, onSubmit, loading }: { users: any[]; substances: any[]; onSubmit: (payload: any) => Promise<unknown>; loading: boolean }) {
  return (
    <form
      className="space-y-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const fd = new FormData(e.currentTarget);
        await onSubmit({
          user_id: String(fd.get("user_id") || ""),
          substance_id: String(fd.get("substance_id") || ""),
          log_date: String(fd.get("log_date") || ""),
          craving_level: Number(fd.get("craving_level") || 0),
          quantity_used: fd.get("quantity_used") ? Number(fd.get("quantity_used")) : null,
          mood_score: fd.get("mood_score") ? Number(fd.get("mood_score")) : null,
          cbt_notes: String(fd.get("cbt_notes") || ""),
          trigger_notes: String(fd.get("trigger_notes") || ""),
        });
        e.currentTarget.reset();
      }}
    >
      <div className="grid gap-4 md:grid-cols-2">
        <Field label="Utilisateur">
          <select name="user_id" className={inputClassName()} required>
            <option value="">Choisir</option>
            {users.map((user) => <option key={user.id} value={user.id}>{user.first_name} {user.last_name}</option>)}
          </select>
        </Field>
        <Field label="Substance">
          <select name="substance_id" className={inputClassName()} required>
            <option value="">Choisir</option>
            {substances.map((substance) => <option key={substance.id} value={substance.id}>{substance.name}</option>)}
          </select>
        </Field>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Field label="Date"><input type="date" name="log_date" className={inputClassName()} required /></Field>
        <Field label="Craving (0-10)"><input type="number" name="craving_level" min={0} max={10} className={inputClassName()} required /></Field>
        <Field label="Mood (0-10)"><input type="number" name="mood_score" min={0} max={10} className={inputClassName()} /></Field>
      </div>
      <Field label="Quantité utilisée"><input type="number" name="quantity_used" className={inputClassName()} /></Field>
      <Field label="Notes TCC"><textarea name="cbt_notes" className={inputClassName()} rows={3} /></Field>
      <Field label="Déclencheurs"><textarea name="trigger_notes" className={inputClassName()} rows={3} /></Field>
      <button className={buttonClassName(loading)} disabled={loading}>{loading ? "Enregistrement..." : "Créer le log"}</button>
    </form>
  );
}

function AssessmentForm({ substances, onSubmit, loading }: { substances: any[]; onSubmit: (payload: any) => Promise<unknown>; loading: boolean }) {
  return (
    <form
      className="space-y-4"
      onSubmit={async (e) => {
        e.preventDefault();
        const fd = new FormData(e.currentTarget);
        await onSubmit({
          craving_level: Number(fd.get("craving_level") || 0),
          substance_name: String(fd.get("substance_name") || ""),
          city: String(fd.get("city") || ""),
          postal_code: String(fd.get("postal_code") || ""),
          cbt_notes: String(fd.get("cbt_notes") || ""),
        });
      }}
    >
      <Field label="Substance">
        <select name="substance_name" className={inputClassName()} required>
          <option value="">Choisir</option>
          {substances.map((substance) => <option key={substance.id} value={substance.name}>{substance.name}</option>)}
        </select>
      </Field>
      <Field label="Craving (0-10)"><input type="number" name="craving_level" min={0} max={10} className={inputClassName()} required /></Field>
      <div className="grid gap-4 md:grid-cols-2">
        <Field label="Ville"><input name="city" className={inputClassName()} defaultValue="Angers" /></Field>
        <Field label="Code postal"><input name="postal_code" className={inputClassName()} defaultValue="49000" /></Field>
      </div>
      <Field label="Contexte TCC"><textarea name="cbt_notes" className={inputClassName()} rows={3} /></Field>
      <button className={buttonClassName(loading)} disabled={loading}>{loading ? "Évaluation..." : "Lancer l'évaluation"}</button>
    </form>
  );
}

function AssessmentPanel({ result }: { result: AssessmentResult }) {
  return (
    <div className="mt-5 rounded-xl border border-sky-900 bg-sky-950/40 p-4 text-sm space-y-3">
      <div>
        <span className="font-semibold">Route :</span> {result.route}
      </div>
      <div>
        <span className="font-semibold">Sévérité :</span> {result.payload.severity}
      </div>
      {result.payload.exercise ? (
        <div className="space-y-2">
          <div className="font-semibold">Exercice TCC : {result.payload.exercise.name}</div>
          <ol className="list-decimal pl-5 space-y-1 text-slate-200">
            {result.payload.exercise.steps.map((step) => <li key={step}>{step}</li>)}
          </ol>
        </div>
      ) : null}
      {result.payload.message ? <div>{result.payload.message}</div> : null}
      {result.payload.local_resource ? (
        <div className="space-y-1">
          <div><span className="font-semibold">Ressource :</span> {result.payload.local_resource.type}</div>
          <div><span className="font-semibold">Recherche :</span> {result.payload.local_resource.search_hint}</div>
          <a className="text-sky-300 underline" href={result.payload.local_resource.directory_url} target="_blank" rel="noreferrer">
            Ouvrir l'annuaire CSAPA
          </a>
        </div>
      ) : null}
    </div>
  );
}
