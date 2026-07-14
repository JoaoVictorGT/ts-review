import React, { useState } from "react";
import {
  ShieldCheck,
  TrendingUp,
  Search,
  Check,
  Star,
  Lock,
  Mail,
  X,
  ChevronRight,
} from "lucide-react";

const HOTELS = [
  { id: 1, name: "Grand Azure Palace", quadrant: "premium", x: 82, y: 18, price: 620, food: 4.7, service: 4.9, comfort: 4.8, cleaner: 4.9 },
  { id: 2, name: "Hotel Meridian Bay", quadrant: "premium", x: 74, y: 24, price: 540, food: 4.5, service: 4.6, comfort: 4.7, cleaner: 4.8 },
  { id: 3, name: "The Ivory Court", quadrant: "value", x: 78, y: 74, price: 210, food: 4.4, service: 4.6, comfort: 4.3, cleaner: 4.7 },
  { id: 4, name: "Cedar & Stone Inn", quadrant: "value", x: 70, y: 68, price: 180, food: 4.2, service: 4.5, comfort: 4.2, cleaner: 4.4 },
  { id: 5, name: "Downtown Basic Suites", quadrant: "basic", x: 28, y: 78, price: 95, food: 3.1, service: 3.2, comfort: 3.0, cleaner: 3.4 },
  { id: 6, name: "Traveler's Lodge", quadrant: "basic", x: 22, y: 84, price: 80, food: 2.9, service: 3.0, comfort: 3.1, cleaner: 3.2 },
  { id: 7, name: "Regal Overlook Hotel", quadrant: "overpriced", x: 26, y: 20, price: 480, food: 2.8, service: 3.0, comfort: 3.2, cleaner: 2.9 },
  { id: 8, name: "Marbella Grand", quadrant: "overpriced", x: 34, y: 28, price: 410, food: 3.1, service: 2.9, comfort: 3.0, cleaner: 3.1 },
];

const QUADRANT_STYLES = {
  premium: { label: "Premium / Luxo", badge: "bg-emerald-50 text-emerald-700 border border-emerald-200" },
  value: { label: "Custo-Benefício", badge: "bg-sky-50 text-sky-700 border border-sky-200" },
  basic: { label: "Econômico Básico", badge: "bg-slate-50 text-slate-600 border border-slate-200" },
  overpriced: { label: "Sobreavaliado", badge: "bg-amber-50 text-amber-700 border border-amber-200" },
};

function Logo({ light }) {
  return (
    <div className="flex items-center gap-2">
      <div className="relative w-7 h-7 flex items-center justify-center">
        <Star className="w-7 h-7 text-sky-400" strokeWidth={1.75} />
        <Check className="w-3.5 h-3.5 text-blue-600 absolute" strokeWidth={3} />
      </div>
      <span className={`text-lg font-semibold tracking-tight ${light ? "text-white" : "text-slate-900"}`}>
        TrueStay
      </span>
    </div>
  );
}

function Header({ page, setPage }) {
  const links = [
    { id: "home", label: "Metodologia" },
    { id: "quadrant", label: "Quadrante" },
    { id: "pricing", label: "Planos" },
  ];
  return (
    <header className="sticky top-0 z-30 bg-white/80 backdrop-blur-md border-b border-slate-100">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <button onClick={() => setPage("home")}>
          <Logo />
        </button>
        <nav className="hidden md:flex items-center gap-8">
          {links.map((l) => (
            <button
              key={l.id}
              onClick={() => setPage(l.id)}
              className={`text-sm transition-colors ${
                page === l.id ? "text-blue-600 font-medium" : "text-slate-600 hover:text-blue-600"
              }`}
            >
              {l.label}
            </button>
          ))}
        </nav>
        <button
          onClick={() => setPage("login")}
          className="text-sm font-medium text-blue-600 border border-blue-200 rounded-lg px-4 py-2 hover:bg-blue-50 transition-colors"
        >
          Entrar
        </button>
      </div>
    </header>
  );
}

function HomePage({ setPage }) {
  const methodology = [
    { icon: ShieldCheck, title: "Auditoria Independente", text: "Cada estadia é verificada por auditores externos, sem interferência dos hotéis avaliados." },
    { icon: TrendingUp, title: "4 Dimensões de Dados", text: "Food, Service, Comfort e Cleaner são medidos e ponderados em um score único e comparável." },
    { icon: Search, title: "Zero Reviews Falsas", text: "Metodologia fechada que elimina avaliações manipuladas, ao contrário de plataformas abertas." },
  ];
  return (
    <div>
      <section className="relative overflow-hidden">
        <div
          className="absolute inset-0"
          style={{ background: "radial-gradient(circle at 50% 0%, #f8fafc 0%, #ffffff 60%)" }}
        />
        <div className="relative max-w-4xl mx-auto px-6 pt-24 pb-20 text-center">
          <div className="inline-flex items-center gap-2 text-xs font-medium text-blue-600 bg-blue-50 border border-blue-100 rounded-full px-3 py-1 mb-6">
            <ShieldCheck className="w-3.5 h-3.5" /> O Gartner da Hotelaria
          </div>
          <h1 className="text-5xl md:text-6xl font-semibold text-slate-900 leading-tight tracking-tight">
            Inteligência e{" "}
            <span className="bg-gradient-to-r from-sky-400 to-blue-600 bg-clip-text text-transparent">
              Confiança
            </span>{" "}
            para decisões hoteleiras
          </h1>
          <p className="mt-6 text-lg text-slate-500 max-w-2xl mx-auto">
            Verified Reviews. Trusted Stays. Classificamos hotéis com a mesma rigidez analítica do
            Magic Quadrant, para que gestores de viagens decidam com dados, não com opiniões.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <button
              onClick={() => setPage("quadrant")}
              className="bg-gradient-to-r from-sky-400 to-blue-600 text-white text-sm font-medium rounded-lg px-6 py-3 shadow-sm hover:shadow-md transition-shadow"
            >
              Ver Quadrante TrueStay
            </button>
            <button
              onClick={() => setPage("pricing")}
              className="text-sm font-medium text-slate-700 border border-slate-200 rounded-lg px-6 py-3 hover:bg-slate-50 transition-colors"
            >
              Ver planos
            </button>
          </div>
        </div>
      </section>

      <section className="max-w-6xl mx-auto px-6 pb-24">
        <p className="text-center text-xs font-semibold tracking-wider text-slate-400 uppercase mb-10">
          Metodologia TrueStay
        </p>
        <div className="grid md:grid-cols-3 gap-6">
          {methodology.map((m) => (
            <div
              key={m.title}
              className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              <div className="w-10 h-10 rounded-lg bg-sky-50 flex items-center justify-center mb-4">
                <m.icon className="w-5 h-5 text-sky-500" strokeWidth={1.75} />
              </div>
              <h3 className="text-slate-900 font-medium mb-2">{m.title}</h3>
              <p className="text-sm text-slate-500 leading-relaxed">{m.text}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function PricingPage() {
  const plans = [
    {
      name: "Starter",
      price: "R$ 0",
      period: "/mês",
      desc: "Para conhecer o quadrante público.",
      features: ["Acesso ao quadrante geral", "1 relatório resumido por mês", "Suporte por e-mail"],
      cta: "Começar grátis",
      highlight: false,
    },
    {
      name: "Hotel Partner",
      price: "R$ 1.490",
      period: "/mês",
      desc: "Para gestores de viagens corporativas.",
      features: [
        "Relatórios consolidados ilimitados",
        "Selo TrueStay licenciado",
        "Benchmarking vs. concorrentes",
        "Suporte prioritário",
      ],
      cta: "Assinar Hotel Partner",
      highlight: true,
    },
    {
      name: "Corporate",
      price: "Sob consulta",
      period: "",
      desc: "Para redes e agências de luxo.",
      features: [
        "Tudo do Hotel Partner",
        "Consultoria de diagnóstico dedicada",
        "Integração via API",
        "Gerente de conta exclusivo",
      ],
      cta: "Falar com especialista",
      highlight: false,
    },
  ];
  return (
    <div className="max-w-6xl mx-auto px-6 py-20">
      <div className="text-center mb-14">
        <h1 className="text-3xl font-semibold text-slate-900">Planos e ofertas</h1>
        <p className="text-slate-500 mt-3">Escolha o acesso certo à inteligência hoteleira TrueStay.</p>
      </div>
      <div className="grid md:grid-cols-3 gap-6 items-start">
        {plans.map((p) => (
          <div
            key={p.name}
            className={`relative bg-white rounded-xl p-8 ${
              p.highlight
                ? "border-2 border-blue-500 shadow-md"
                : "border border-slate-200 shadow-sm"
            }`}
          >
            {p.highlight && (
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-600 text-white text-xs font-medium rounded-full px-3 py-1">
                Mais Popular
              </span>
            )}
            <h3 className="text-slate-900 font-medium">{p.name}</h3>
            <p className="text-sm text-slate-500 mt-1 mb-6">{p.desc}</p>
            <div className="flex items-baseline gap-1 mb-6">
              <span className="text-3xl font-semibold text-slate-900">{p.price}</span>
              <span className="text-sm text-slate-400">{p.period}</span>
            </div>
            <ul className="space-y-3 mb-8">
              {p.features.map((f) => (
                <li key={f} className="flex items-start gap-2 text-sm text-slate-600">
                  <Check className="w-4 h-4 text-sky-500 mt-0.5 shrink-0" strokeWidth={2.5} />
                  {f}
                </li>
              ))}
            </ul>
            <button
              className={`w-full text-sm font-medium rounded-lg py-2.5 transition-shadow ${
                p.highlight
                  ? "bg-gradient-to-r from-sky-400 to-blue-600 text-white shadow-sm hover:shadow-md"
                  : "bg-slate-900 text-white hover:bg-slate-800"
              }`}
            >
              {p.cta}
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

function LoginPage() {
  return (
    <div className="min-h-[640px] grid md:grid-cols-2">
      <div className="relative bg-slate-900 hidden md:flex flex-col justify-between p-12 overflow-hidden">
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage:
              "radial-gradient(circle at 20% 20%, #38bdf8 0%, transparent 40%), radial-gradient(circle at 80% 70%, #2563eb 0%, transparent 45%)",
          }}
        />
        <div className="relative">
          <Logo light />
        </div>
        <div className="relative">
          <p className="text-2xl text-white leading-snug max-w-sm">
            Acesse a maior plataforma de inteligência hoteleira do mundo.
          </p>
          <p className="text-sm text-blue-200 mt-4">Verified Reviews. Trusted Stays.</p>
        </div>
      </div>
      <div className="flex items-center justify-center p-10">
        <div className="w-full max-w-sm">
          <div className="md:hidden mb-8">
            <Logo />
          </div>
          <h1 className="text-2xl font-semibold text-slate-900 mb-1">Bem-vindo de volta</h1>
          <p className="text-sm text-slate-500 mb-8">Entre para acessar seus relatórios.</p>
          <div className="space-y-4">
            <div>
              <label className="text-xs font-medium text-slate-600">E-mail corporativo</label>
              <div className="mt-1 relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="email"
                  placeholder="voce@empresa.com"
                  className="w-full rounded-lg border border-slate-200 pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
                />
              </div>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600">Senha</label>
              <div className="mt-1 relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="password"
                  placeholder="••••••••"
                  className="w-full rounded-lg border border-slate-200 pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-sky-400"
                />
              </div>
            </div>
            <button className="w-full bg-gradient-to-r from-sky-400 to-blue-600 text-white text-sm font-medium rounded-lg py-2.5 shadow-sm hover:shadow-md transition-shadow">
              Entrar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricBar({ label, value }) {
  const pct = Math.round((value / 5) * 100);
  return (
    <div className="mb-4">
      <div className="flex justify-between text-xs mb-1.5">
        <span className="text-slate-600">{label}</span>
        <span className="text-slate-900 font-medium">{value.toFixed(1)}/5</span>
      </div>
      <div className="h-2 rounded-full bg-slate-100 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-sky-400 to-blue-600"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function QuadrantPage() {
  const [selected, setSelected] = useState(null);
  const [hovered, setHovered] = useState(null);

  return (
    <div className="max-w-6xl mx-auto px-6 py-16">
      <div className="mb-10">
        <h1 className="text-3xl font-semibold text-slate-900">Quadrante TrueStay</h1>
        <p className="text-slate-500 mt-2">Preço da diária x desempenho auditado nas 4 dimensões.</p>
      </div>

      <div className="grid lg:grid-cols-[1fr_auto] gap-8 items-start">
        <div className="relative aspect-square bg-slate-50 rounded-xl border border-slate-200 p-8">
          <div className="absolute inset-8 border-l border-b border-dashed border-slate-300" />
          <div className="absolute inset-8 left-1/2 top-8 bottom-8 border-l border-dashed border-slate-300" />
          <div className="absolute inset-8 top-1/2 left-8 right-8 border-t border-dashed border-slate-300" />

          <span className="absolute top-4 left-8 text-xs font-semibold text-slate-400 tracking-wider uppercase">
            Sobreavaliados
          </span>
          <span className="absolute top-4 right-8 text-xs font-semibold text-slate-400 tracking-wider uppercase">
            Premium / Luxo
          </span>
          <span className="absolute bottom-4 left-8 text-xs font-semibold text-slate-400 tracking-wider uppercase">
            Econômicos Básicos
          </span>
          <span className="absolute bottom-4 right-8 text-xs font-semibold text-slate-400 tracking-wider uppercase">
            Custo-Benefício
          </span>

          <span className="absolute left-2 top-1/2 -translate-y-1/2 -rotate-90 text-xs text-slate-400">
            Preço
          </span>
          <span className="absolute bottom-2 right-1/2 translate-x-1/2 text-xs text-slate-400">
            Qualidade auditada
          </span>

          {HOTELS.map((h) => (
            <button
              key={h.id}
              onMouseEnter={() => setHovered(h.id)}
              onMouseLeave={() => setHovered(null)}
              onClick={() => setSelected(h)}
              className="absolute rounded-full bg-blue-600 ring-4 ring-white shadow-md transition-all"
              style={{
                left: `${h.x}%`,
                top: `${h.y}%`,
                width: hovered === h.id ? 16 : 12,
                height: hovered === h.id ? 16 : 12,
                transform: "translate(-50%, -50%)",
              }}
            >
              {hovered === h.id && (
                <span className="absolute left-1/2 -translate-x-1/2 -top-8 whitespace-nowrap bg-slate-900 text-white text-xs rounded-md px-2 py-1">
                  {h.name}
                </span>
              )}
            </button>
          ))}
        </div>

        <div className="w-full lg:w-72 bg-white border border-slate-200 rounded-xl p-5">
          <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase mb-3">Legenda</p>
          {Object.entries(QUADRANT_STYLES).map(([key, q]) => (
            <div key={key} className="flex items-center gap-2 mb-2 text-sm">
              <span className={`w-2 h-2 rounded-full ${
                key === "premium" ? "bg-emerald-500" : key === "value" ? "bg-sky-500" : key === "basic" ? "bg-slate-400" : "bg-amber-500"
              }`} />
              <span className="text-slate-600">{q.label}</span>
            </div>
          ))}
          <p className="text-xs text-slate-400 mt-4 leading-relaxed">
            Clique em um hotel no gráfico para abrir o relatório detalhado.
          </p>
        </div>
      </div>

      {selected && (
        <div className="fixed inset-0 z-40 flex justify-end">
          <div
            className="absolute inset-0 bg-slate-900/30"
            onClick={() => setSelected(null)}
          />
          <div className="relative w-full max-w-sm bg-white h-full shadow-xl p-8 overflow-y-auto">
            <button
              onClick={() => setSelected(null)}
              className="absolute top-6 right-6 text-slate-400 hover:text-slate-600"
              aria-label="Fechar"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="w-full h-32 rounded-lg bg-gradient-to-br from-sky-100 to-blue-100 mb-6" />

            <span
              className={`inline-block text-xs font-medium rounded-full px-3 py-1 mb-3 ${
                QUADRANT_STYLES[selected.quadrant].badge
              }`}
            >
              {QUADRANT_STYLES[selected.quadrant].label}
            </span>
            <h2 className="text-xl font-semibold text-slate-900 mb-1">{selected.name}</h2>
            <p className="text-sm text-slate-500 mb-8">Diária média: R$ {selected.price}</p>

            <p className="text-xs font-semibold text-slate-400 tracking-wider uppercase mb-4">
              Desempenho auditado
            </p>
            <MetricBar label="Food" value={selected.food} />
            <MetricBar label="Service" value={selected.service} />
            <MetricBar label="Comfort" value={selected.comfort} />
            <MetricBar label="Cleaner" value={selected.cleaner} />

            <button className="w-full mt-6 flex items-center justify-center gap-2 bg-slate-900 text-white text-sm font-medium rounded-lg py-2.5 hover:bg-slate-800 transition-colors">
              Ver relatório completo <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function TrueStayApp() {
  const [page, setPage] = useState("home");
  return (
    <div className="min-h-screen bg-slate-50 font-sans">
      <Header page={page} setPage={setPage} />
      {page === "home" && <HomePage setPage={setPage} />}
      {page === "pricing" && <PricingPage />}
      {page === "login" && <LoginPage />}
      {page === "quadrant" && <QuadrantPage />}
    </div>
  );
}
