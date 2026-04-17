"""
╔══════════════════════════════════════════════════════════════╗
║        N1 AGENT v5 — AI Development Platform                 ║
║   Telegram Bot | Multi-AI Orchestrator | 62 Modules          ║
╚══════════════════════════════════════════════════════════════╝

Requirements:
    pip install python-telegram-bot openai aiohttp

Run:
    export OPENAI_API_KEY="sk-your-key"
    python3 n1_agent_v5.py
"""

# ══════════════════════════════════════════════════════════════
#  IMPORTS
# ══════════════════════════════════════════════════════════════
import os
import sys
import json
import time
import logging
import asyncio
import hashlib
import tempfile
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from openai import OpenAI
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from telegram.constants import ParseMode, ChatAction

# ══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ══════════════════════════════════════════════════════════════
BOT_TOKEN  = "8753607198:AAH3CI5nYbk2nV_NB06yGCTm0AkSBK_64bk"
OPENAI_KEY = os.getenv("OPENAI_API_KEY", "sk-REPLACE_ME")
OWNER_ID   = 8670552926

DATA_DIR   = Path("n1_data")
PROJ_DIR   = DATA_DIR / "projects"
MEM_DIR    = DATA_DIR / "memory"
PLUGIN_DIR = DATA_DIR / "plugins"

for d in [DATA_DIR, PROJ_DIR, MEM_DIR, PLUGIN_DIR]:
    d.mkdir(parents=True, exist_ok=True)

client = OpenAI(api_key=OPENAI_KEY)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
log = logging.getLogger("N1AGENT")

# ══════════════════════════════════════════════════════════════
#  CONSTANTS (preserved from v1)
# ══════════════════════════════════════════════════════════════
DIALECT_NAMES = {
    "msa":  "فصحى (MSA)",
    "egy":  "مصري 🇪🇬",
    "gulf": "خليجي 🇸🇦",
    "lev":  "شامي 🇸🇾",
}

MODES = {
    "safe": {
        "label": "🟢 SAFE MODE",
        "desc":  "ردود محققة ودقيقة — مناسب للعمل اليومي.",
        "instruction": (
            "أنت في SAFE MODE. تحقق من كل إجابة قبل إرسالها."
            " كن دقيقاً ومفيداً دون مبالغة."
        ),
    },
    "dev": {
        "label": "🟡 DEV MODE",
        "desc":  "metadata تقني مع كل رد — للمطورين.",
        "instruction": (
            "أنت في DEV MODE. أضف metadata تقني في نهاية كل رد:"
            " (tokens_used, model, latency_sim, agents_triggered)."
            " كن مفصلاً تقنياً."
        ),
    },
    "dark": {
        "label": "🔴 DARK OPS MODE",
        "desc":  "تحليل عميق وأسرع مسار — للمهام الحرجة.",
        "instruction": (
            "أنت في DARK OPS MODE. فكّر بعمق متعدد الطبقات."
            " أعطِ أدق وأقوى حل في أقل خطوات ممكنة."
            " لا حشو، فقط نتائج."
        ),
    },
}

TIERS = {
    "FREE":  {"max_history": 6,  "label": "🆓 FREE"},
    "PRO":   {"max_history": 20, "label": "💎 PRO"},
    "OWNER": {"max_history": 50, "label": "👑 OWNER"},
}

# ══════════════════════════════════════════════════════════════
#  v3: MULTI-AI MODEL ROUTING
# ══════════════════════════════════════════════════════════════
MODEL_ROUTING = {
    "coding":    "gpt-4o",
    "reasoning": "gpt-4o",
    "fast":      "gpt-4o-mini",
    "testing":   "gpt-4o-mini",
    "debug":     "gpt-4o",
    "security":  "gpt-4o",
    "default":   "gpt-4o-mini",
}
MODEL_FALLBACK = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]

def route_model(agents: List[str]) -> str:
    if any(a in ("DEBUG", "ARCHITECT", "SECURITY", "SCANNER") for a in agents):
        return MODEL_ROUTING["reasoning"]
    if any(a in ("CODER", "REFACTOR") for a in agents):
        return MODEL_ROUTING["coding"]
    if "TEST" in agents:
        return MODEL_ROUTING["testing"]
    return MODEL_ROUTING["default"]

async def ask_ai_multi(user: dict, message: str, model: str, agents: List[str]) -> str:
    max_h    = TIERS[user["tier"]]["max_history"]
    messages = [
        {"role": "system", "content": build_system_prompt(user, agents)}
    ] + user["history"][-max_h * 2:]
    for attempt_model in [model] + [m for m in MODEL_FALLBACK if m != model]:
        try:
            resp = client.chat.completions.create(
                model=attempt_model, messages=messages,
                max_tokens=2000, temperature=0.7,
            )
            if attempt_model != model:
                add_log(f"MODEL_FALLBACK from={model} to={attempt_model}")
            return resp.choices[0].message.content
        except Exception as e:
            add_log(f"MODEL_FAIL model={attempt_model}: {str(e)[:80]}", "WARN")
    return "⚠️ جميع النماذج غير متاحة حالياً."

async def compare_models(message: str, user: dict) -> str:
    agents = route_agents(message)
    sys_p  = build_system_prompt(user, agents)
    msgs   = [{"role": "system", "content": sys_p}, {"role": "user", "content": message}]
    results = {}
    for model in ["gpt-4o-mini", "gpt-4o"]:
        try:
            r = client.chat.completions.create(model=model, messages=msgs, max_tokens=800)
            results[model] = r.choices[0].message.content
        except Exception as e:
            results[model] = f"خطأ: {str(e)[:80]}"
    out  = "⚖️ *مقارنة النماذج:*\n\n"
    out += f"**🔵 gpt-4o-mini:**\n{results.get('gpt-4o-mini','—')[:600]}\n\n"
    out += f"**🟣 gpt-4o:**\n{results.get('gpt-4o','—')[:600]}"
    return out

# ── v3: Extended Agents ──────────────────────────────────────
AGENTS = {
    "CODER":      "توليد كود احترافي جاهز للإنتاج",
    "DEBUG":      "تحليل الأخطاء والأسباب الجذرية وإصلاحها",
    "TEST":       "توليد حالات اختبار وـ edge cases",
    "OPTIMIZER":  "تحسين الأداء والمعمارية",
    "EXPLAINER":  "تبسيط المفاهيم التقنية",
    "SECURITY":   "الأمن الدفاعي وكشف التهديدات",
    "REFACTOR":   "إعادة هيكلة الكود وتنظيفه",
    "ARCHITECT":  "تصميم البنية المعمارية والقواعد",
    "ANALYST":    "تحليل الكود وفهم البنية الكاملة",
    "PAIR":       "مساعد برمجة تفاعلي خطوة بخطوة",
    "PROFILER":   "تحليل الأداء واكتشاف الـ bottlenecks",
    "SCANNER":    "فحص الأمان واكتشاف الثغرات",
    "DOCUMENTER": "توليد التوثيق والـ README",
    "SELF":       "تحليل النظام وتحسين نفسه",
}

# Agent role-specific behavior (Feature #9 — True Agent Behavior)
AGENT_ROLES = {
    "CODER":     "أنت مبرمج خبير. ركّز على كتابة كود نظيف، موثق، وجاهز للإنتاج. اتبع best practices دائماً.",
    "DEBUG":     "أنت محقق أخطاء متخصص. حدد السطر المشكل بدقة، اشرح السبب الجذري، وقدم الحل الأمثل.",
    "TEST":      "أنت مهندس جودة. اكتب اختبارات شاملة تغطي الحالات الاعتيادية والحدية والأخطاء.",
    "OPTIMIZER": "أنت خبير أداء. حلل نقاط الضعف وقدم تحسينات قابلة للقياس مع أمثلة كود.",
    "EXPLAINER": "أنت معلم تقني. اشرح بأسلوب واضح مع أمثلة عملية، من البسيط للمعقد.",
    "SECURITY":  "أنت خبير أمن دفاعي. كشف الثغرات وقدم حلول أمنية فقط — لا هجمات.",
    "REFACTOR":  "أنت خبير clean code. طبق SOLID وDRY وKISS، أضف type hints وتعليقات واضحة.",
    "ARCHITECT": "أنت مهندس معمارية. صمم أنظمة قابلة للتوسع مع مراعاة الأداء والأمان.",
    "ANALYST":   "أنت محلل كود. افهم البنية الكاملة، استخرج التبعيات، وقيّم الجودة.",
    "PAIR":       "أنت شريك برمجة. اعمل تفاعلياً، اطرح أسئلة توضيحية، وفكّر بصوت عالٍ.",
    "PROFILER":   "أنت خبير أداء. حدد الـ bottlenecks، قدّر Big O، واقترح تحسينات قابلة للقياس.",
    "SCANNER":    "أنت خبير أمن. افحص OWASP Top 10 والثغرات الشائعة — أمن دفاعي فقط.",
    "DOCUMENTER": "أنت كاتب توثيق. اكتب README واضحاً، docstrings شاملة، API docs منظمة.",
    "SELF":       "أنت محلل ذاتي. حلّل كود النظام، اكتشف نقاط الضعف، اقترح تحسينات بنيوية.",
}

EGY_MARKERS  = ["ازيك","عامل","ايه","مش","دلوقتي","كمان","بقى","عشان",
                 "لازم","احنا","انتو","مفيش","فيه","هيه","يعني","طيب",
                 "هنا","ده","دي","دول","اللي","هو","هي"]
GULF_MARKERS = ["شلونك","وش","ليش","ابي","حق","يبا","زين","عيل",
                 "عساك","وايد","شفيق","هالحين","اكو","ماكو"]
LEV_MARKERS  = ["شو","كيفك","مني","هيدا","هيدي","يلا","ما في",
                 "هلق","بدي","رح","ما بعرف","هيك","منيح"]

# Feature #18 — Context Awareness: Project type patterns
PROJECT_TYPES = {
    "web":      ["html","css","javascript","js","react","vue","angular","frontend","backend","express","django","flask","fastapi","node"],
    "mobile":   ["flutter","react native","android","ios","kotlin","swift","dart"],
    "data":     ["pandas","numpy","matplotlib","sklearn","tensorflow","pytorch","dataset","machine learning","ml","data science"],
    "devops":   ["docker","kubernetes","k8s","ci/cd","github actions","terraform","ansible","nginx","pipeline"],
    "database": ["sql","mysql","postgresql","mongodb","redis","sqlite","orm","schema","migration"],
    "security": ["pentest","vulnerability","exploit","security","audit","cvss","owasp"],
    "api":      ["api","rest","graphql","grpc","endpoint","swagger","openapi","webhook"],
    "system":   ["c++","c","rust","assembly","kernel","os","embedded","firmware"],
}

# ══════════════════════════════════════════════════════════════
#  MODULE #8: PLUGIN SYSTEM
# ══════════════════════════════════════════════════════════════
class PluginManager:
    """Modular plugin system for extending bot capabilities (Feature #8)."""

    def __init__(self):
        self.plugins: Dict[str, dict] = {}
        self.hooks: Dict[str, list] = {
            "pre_message": [],
            "post_message": [],
            "pre_ai": [],
            "post_ai": [],
        }

    def register(self, name: str, plugin: dict):
        self.plugins[name] = plugin
        for hook, handler in plugin.get("hooks", {}).items():
            if hook in self.hooks:
                self.hooks[hook].append(handler)
        log.info(f"PLUGIN_REGISTERED: {name}")

    def list_plugins(self) -> List[str]:
        return list(self.plugins.keys())

    async def run_hook(self, hook: str, context: dict) -> dict:
        for handler in self.hooks.get(hook, []):
            try:
                result = handler(context)
                if asyncio.iscoroutine(result):
                    context = await result or context
                else:
                    context = result or context
            except Exception as e:
                log.error(f"PLUGIN_ERROR hook={hook}: {e}")
        return context


plugin_manager = PluginManager()

# ══════════════════════════════════════════════════════════════
#  IN-MEMORY DATABASE (enhanced from v1)
# ══════════════════════════════════════════════════════════════
users:    Dict[int, dict] = {}
sys_logs: List[str]       = []


def get_user(uid: int) -> dict:
    if uid not in users:
        users[uid] = {
            # ── v1 fields (preserved) ──
            "lang":          "ar",
            "dialect":       "egy",
            "mode":          "safe",
            "history":       [],
            "tier":          "OWNER" if uid == OWNER_ID else "FREE",
            "created_at":    datetime.now().isoformat(),
            "last_seen":     datetime.now().isoformat(),
            "message_count": 0,
            "long_term": {
                "preferences":     [],
                "project_history": [],
                "patterns":        [],
            },
            # ── v2: Smart Memory (Feature #3) ──
            "structured_memory": {
                "preferences":     {},   # key → value preferences
                "past_errors":     [],   # {code, error, time}
                "project_context": {},   # current project context
                "learned_fixes":   {},   # error_hash → fix summary
                "pair_mode":       False,
                "current_project": None,
            },
            # ── v2: Error Learning (Feature #13) ──
            "error_patterns": {},        # error_hash → {count, last_fix}
            # ── v2: Context Awareness (Feature #18) ──
            "detected_project_type": None,
            # ── v2: Task tracking (Features #19, #20) ──
            "active_tasks":  [],
            "task_history":  [],
        }
        _load_user_memory(uid)

    users[uid]["last_seen"]     = datetime.now().isoformat()
    users[uid]["message_count"] += 1
    return users[uid]


def _load_user_memory(uid: int):
    mem_file = MEM_DIR / f"{uid}.json"
    if mem_file.exists():
        try:
            with open(mem_file) as f:
                saved = json.load(f)
            users[uid]["structured_memory"] = saved.get(
                "structured_memory", users[uid]["structured_memory"]
            )
            users[uid]["error_patterns"] = saved.get("error_patterns", {})
        except Exception as e:
            log.error(f"MEMORY_LOAD_ERROR uid={uid}: {e}")


def save_user_memory(uid: int):
    if uid not in users:
        return
    mem_file = MEM_DIR / f"{uid}.json"
    try:
        with open(mem_file, "w") as f:
            json.dump({
                "structured_memory": users[uid]["structured_memory"],
                "error_patterns":    users[uid]["error_patterns"],
                "last_saved":        datetime.now().isoformat(),
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error(f"MEMORY_SAVE_ERROR uid={uid}: {e}")


def add_log(event: str, level: str = "INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    entry = f"[{ts}][{level}] {event}"
    sys_logs.append(entry)
    if len(sys_logs) > 200:
        sys_logs.pop(0)
    log.info(event)

# ══════════════════════════════════════════════════════════════
#  DETECTION HELPERS (preserved + enhanced)
# ══════════════════════════════════════════════════════════════
def detect_language(text: str) -> str:
    arabic = sum(1 for c in text if '\u0600' <= c <= '\u06ff')
    return "ar" if arabic > len(text) * 0.25 else "en"


def detect_dialect(text: str) -> str:
    t = text.lower()
    for m in EGY_MARKERS:
        if m in t: return "egy"
    for m in GULF_MARKERS:
        if m in t: return "gulf"
    for m in LEV_MARKERS:
        if m in t: return "lev"
    return "msa"


def detect_project_type(text: str) -> Optional[str]:
    """Feature #18 — Detect project type from message content."""
    text_l = text.lower()
    scores = {}
    for ptype, keywords in PROJECT_TYPES.items():
        score = sum(1 for kw in keywords if kw in text_l)
        if score > 0:
            scores[ptype] = score
    return max(scores, key=scores.get) if scores else None


def route_agents(text: str) -> List[str]:
    """Route input to relevant agents — Feature #9 True Agent Behavior."""
    text_l = text.lower()
    triggered = []

    code_kw     = ["كود","برمج","اكتب","function","class","script","python","js","api","sql","بايثون"]
    debug_kw    = ["خطأ","error","bug","مش شغال","فشل","exception","traceback","crash"]
    test_kw     = ["test","اختبر","unit test","edge case","تحقق","verify"]
    optim_kw    = ["optimize","سرّع","improve","أحسن","performance","refactor","تحسين"]
    explain_kw  = ["اشرح","explain","ايه معنى","كيف يعمل","what is","how does","ما هو"]
    security_kw = ["security","أمان","hacking","ثغرة","vulnerability","pentest","exploit"]
    refactor_kw = ["refactor","نظّم","clean","هيكل","restructure","modular","أعد هيكلة"]
    arch_kw     = ["architecture","معمارية","design","database","schema","system design","قاعدة بيانات","بنية"]
    pair_kw     = ["pair","تفاعلي","interactive","step by step","خطوة بخطوة","معي"]

    if any(k in text_l for k in code_kw):     triggered.append("CODER")
    if any(k in text_l for k in debug_kw):    triggered.append("DEBUG")
    if any(k in text_l for k in test_kw):     triggered.append("TEST")
    if any(k in text_l for k in optim_kw):    triggered.append("OPTIMIZER")
    if any(k in text_l for k in explain_kw):  triggered.append("EXPLAINER")
    if any(k in text_l for k in security_kw): triggered.append("SECURITY")
    if any(k in text_l for k in refactor_kw): triggered.append("REFACTOR")
    if any(k in text_l for k in arch_kw):     triggered.append("ARCHITECT")
    if any(k in text_l for k in pair_kw):     triggered.append("PAIR")

    profile_kw  = ["profile","أداء","bottleneck","بطيء","slow","complexity","تعقيد"]
    scan_kw     = ["scan","فحص أمان","ثغرات","owasp","injection","xss","csrf"]
    doc_kw      = ["readme","توثيق","document","وثّق","اشرح الكود","api docs"]
    self_kw     = ["حسّن نفسك","self improve","analyze yourself","حلّل نفسك"]
    if any(k in text_l for k in profile_kw):  triggered.append("PROFILER")
    if any(k in text_l for k in scan_kw):     triggered.append("SCANNER")
    if any(k in text_l for k in doc_kw):      triggered.append("DOCUMENTER")
    if any(k in text_l for k in self_kw):     triggered.append("SELF")

    return triggered if triggered else ["EXPLAINER"]


def score_code_quality(code: str) -> dict:
    """Feature #17 — Code Quality Scoring."""
    score  = 100
    issues = []
    lines  = code.split("\n")

    if len(lines) > 0:
        # Comment ratio
        commented = sum(
            1 for l in lines
            if l.strip().startswith(("#", "//", "/*", "*", "'''", '"""'))
        )
        if len(lines) > 0 and commented / len(lines) < 0.1:
            score -= 10
            issues.append("❌ تعليقات قليلة (< 10٪)")

        # Long functions
        func_len, in_func, long_blocks = 0, False, 0
        for l in lines:
            if re.match(r'\s*(async )?def |function ', l):
                if in_func and func_len > 50:
                    long_blocks += 1
                in_func, func_len = True, 0
            elif in_func:
                func_len += 1
        if long_blocks:
            score -= 5 * long_blocks
            issues.append(f"⚠️ {long_blocks} دالة طويلة جداً (> 50 سطر)")

        # Hardcoded secrets
        hardcoded = sum(
            1 for l in lines
            if re.search(r'password\s*=\s*["\']|secret\s*=\s*["\']|api_key\s*=\s*["\']', l, re.I)
        )
        if hardcoded:
            score -= 15
            issues.append(f"🔴 {hardcoded} قيمة سرية مشفرة مباشرة!")

        # Error handling
        try_count = sum(1 for l in lines if re.match(r'\s*(try:|try\s*{)', l))
        if try_count == 0 and len(lines) > 20:
            score -= 10
            issues.append("⚠️ لا يوجد معالجة للأخطاء (try/except)")

        # Debug prints
        debug_prints = sum(
            1 for l in lines
            if re.search(r'\bprint\s*\(|\bconsole\.log\s*\(', l)
        )
        if debug_prints > 5:
            score -= 5
            issues.append(f"⚠️ {debug_prints} print/console.log للتصحيح")

        # Duplicate code (basic heuristic)
        non_empty = [l.strip() for l in lines if l.strip()]
        if len(non_empty) != len(set(non_empty)) and len(lines) > 10:
            dupes = len(non_empty) - len(set(non_empty))
            if dupes > 3:
                score -= 5
                issues.append(f"⚠️ {dupes} سطر مكرر محتمل")

    score = max(0, min(100, score))

    if score >= 90:   grade = "A+ ممتاز 🏆"
    elif score >= 80: grade = "A جيد جداً ✅"
    elif score >= 70: grade = "B جيد 👍"
    elif score >= 60: grade = "C مقبول ⚠️"
    else:             grade = "D يحتاج تحسين 🔴"

    return {"score": score, "grade": grade, "issues": issues}

# ══════════════════════════════════════════════════════════════
#  MODULE #1: CODE EXECUTION SANDBOX
# ══════════════════════════════════════════════════════════════
EXEC_TIMEOUT    = 10
EXEC_MAX_OUTPUT = 3000

SANDBOX_BLOCKED = [
    "import os", "import sys", "import subprocess", "import shutil",
    "__import__", "exec(", "eval(", "compile(",
    "os.system", "os.popen", "os.remove", "os.rmdir",
    "subprocess", "socket", "requests", "urllib", "importlib",
    "open(", "globals()", "locals()",
]


def is_code_safe(code: str) -> Tuple[bool, str]:
    code_lower = code.lower()
    for blocked in SANDBOX_BLOCKED:
        if blocked.lower() in code_lower:
            return False, f"محظور: `{blocked}`"
    return True, ""


async def execute_code(code: str, language: str = "python") -> dict:
    """Feature #1 — Safe code execution sandbox."""
    if language.lower() not in ("python", "python3"):
        return {"success": False, "output": "", "errors": "Python فقط مدعوم حالياً.", "logs": [], "execution_time": 0}

    safe, reason = is_code_safe(code)
    if not safe:
        return {"success": False, "output": "", "errors": f"🔒 كود محظور: {reason}", "logs": ["SANDBOX: blocked"], "execution_time": 0}

    start = time.time()
    logs  = []

    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            tmp = f.name

        logs.append(f"EXEC: running {tmp}")
        proc = await asyncio.create_subprocess_exec(
            sys.executable, tmp,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=EXEC_TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            return {"success": False, "output": "", "errors": f"⏱️ انتهت مهلة التنفيذ ({EXEC_TIMEOUT}s)", "logs": ["EXEC: timeout"], "execution_time": EXEC_TIMEOUT}
        finally:
            try: os.unlink(tmp)
            except: pass

        t    = round(time.time() - start, 3)
        out  = stdout.decode("utf-8", errors="replace")[:EXEC_MAX_OUTPUT]
        err  = stderr.decode("utf-8", errors="replace")[:EXEC_MAX_OUTPUT]
        logs.append(f"EXEC: done in {t}s, rc={proc.returncode}")
        return {"success": proc.returncode == 0, "output": out, "errors": err, "logs": logs, "execution_time": t}

    except Exception as e:
        return {"success": False, "output": "", "errors": str(e), "logs": ["EXEC: exception"], "execution_time": round(time.time() - start, 3)}

# ══════════════════════════════════════════════════════════════
#  MODULE #2: AUTO TESTING SYSTEM
# ══════════════════════════════════════════════════════════════
async def generate_tests(code: str, user: dict) -> str:
    """Feature #2 — Auto-generate unit tests with edge cases."""
    prompt = f"""أنت خبير اختبار برمجيات.
للكود التالي، اكتب:
1. **Unit Tests** بـ pytest — حالات اعتيادية
2. **Edge Cases** — الحدود والقيم الطرفية
3. **Error Cases** — اختبارات الأخطاء المتوقعة
4. **Integration hints** — ملاحظات التكامل

الكود:
```python
{code[:2500]}
```

اكتب الاختبارات كاملة وقابلة للتشغيل مباشرة بـ `pytest`."""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": AGENT_ROLES["TEST"]},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=1800,
    )
    return resp.choices[0].message.content

# ══════════════════════════════════════════════════════════════
#  MODULE #5: DEBUG MODE UPGRADE
# ══════════════════════════════════════════════════════════════
async def deep_debug(code: str, error: str, user: dict) -> str:
    """Feature #5 — Deep debug with line analysis + Feature #13 error learning."""
    # Check learned fixes cache
    err_hash    = hashlib.md5(error[:100].encode()).hexdigest()[:8]
    cached_fix  = user["structured_memory"]["learned_fixes"].get(err_hash)
    cached_hint = f"\n\n⚡ **تذكير:** نفس الخطأ حدث من قبل. الحل السابق:\n{cached_fix}" if cached_fix else ""

    prompt = f"""أنت خبير debug متقدم.
{cached_hint}

**الخطأ:**
```
{error[:600]}
```

**الكود:**
```python
{code[:2500]}
```

قدّم تحليلاً شاملاً:

### 🔍 تشخيص الخطأ
- نوع الخطأ ولماذا حدث بالضبط

### 📍 السطر المشكل
- السطر رقم كم؟ ولماذا هذا السطر؟

### 🔧 الكود المُصحّح
- الكود بعد الإصلاح كاملاً

### 💡 لماذا حدث هذا؟
- الأسباب الجذرية

### 🛡️ كيف تتجنبه مستقبلاً؟

### ⚠️ نقاط ضعف أخرى في الكود"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": AGENT_ROLES["DEBUG"]},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=1800,
    )
    result = resp.choices[0].message.content

    # Feature #13 — Learn from this error
    fix_match = re.search(r'### 🔧 الكود المُصحّح\n(.+?)(?=###|\Z)', result, re.DOTALL)
    if fix_match:
        fix_summary = fix_match.group(1).strip()[:200]
        user["structured_memory"]["learned_fixes"][err_hash] = fix_summary
        # Track error pattern
        ep = user["error_patterns"].setdefault(err_hash, {"count": 0, "last_fix": ""})
        ep["count"] += 1
        ep["last_fix"] = fix_summary[:100]

    return result

# ══════════════════════════════════════════════════════════════
#  MODULE #6: PROJECT MODE
# ══════════════════════════════════════════════════════════════
def create_project(uid: int, name: str, description: str = "") -> dict:
    """Feature #6 — Create persistent project session."""
    proj_id = hashlib.md5(f"{uid}_{name}_{time.time()}".encode()).hexdigest()[:8]
    project = {
        "id":          proj_id,
        "name":        name,
        "description": description,
        "created_at":  datetime.now().isoformat(),
        "files":       {},
        "context":     {},
        "history":     [],
        "type":        None,
    }
    with open(PROJ_DIR / f"{uid}_{proj_id}.json", "w") as f:
        json.dump(project, f, ensure_ascii=False, indent=2)
    return project


def load_project(uid: int, proj_id: str) -> Optional[dict]:
    path = PROJ_DIR / f"{uid}_{proj_id}.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def save_project(uid: int, project: dict):
    with open(PROJ_DIR / f"{uid}_{project['id']}.json", "w") as f:
        json.dump(project, f, ensure_ascii=False, indent=2)


def list_projects(uid: int) -> List[dict]:
    projects = []
    for f in PROJ_DIR.glob(f"{uid}_*.json"):
        try:
            with open(f) as fp:
                projects.append(json.load(fp))
        except: pass
    return sorted(projects, key=lambda p: p.get("created_at", ""), reverse=True)

# ══════════════════════════════════════════════════════════════
#  MODULE #7: WEB / DOCS SEARCH (RAG-lite)
# ══════════════════════════════════════════════════════════════
async def web_search(query: str) -> str:
    """Feature #7 — Search web via DuckDuckGo for documentation-style answers."""
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                if resp.status == 200:
                    data     = await resp.json(content_type=None)
                    abstract = data.get("AbstractText", "")
                    related  = data.get("RelatedTopics", [])[:4]
                    source   = data.get("AbstractURL", "")

                    result = ""
                    if abstract:
                        result += f"📖 **{abstract[:500]}**\n"
                    if source:
                        result += f"🔗 المصدر: {source}\n"
                    if related:
                        result += "\n🔗 **موضوعات ذات صلة:**\n"
                        for t in related:
                            if isinstance(t, dict) and t.get("Text"):
                                result += f"• {t['Text'][:120]}\n"
                    return result.strip() if result else "لم أجد نتائج محددة."
    except Exception as e:
        return f"تعذّر البحث: {str(e)[:100]}"

# ══════════════════════════════════════════════════════════════
#  MODULE #11: CODE UNDERSTANDING ENGINE
# ══════════════════════════════════════════════════════════════
async def analyze_code(code: str, filename: str = "file") -> str:
    """Feature #11 — Full code architecture analysis."""
    lines     = code.split("\n")
    imports   = [l for l in lines if l.strip().startswith(("import ", "from "))]
    functions = [l for l in lines if re.match(r'\s*(async )?def ', l)]
    classes   = [l for l in lines if re.match(r'\s*class ', l)]
    quality   = score_code_quality(code)

    static = (
        f"**📊 إحصائيات أولية:**\n"
        f"• الأسطر: {len(lines)} | الدوال: {len(functions)} | الكلاسات: {len(classes)}\n"
        f"• الاستيرادات: {len(imports)}\n"
        f"• 🏆 الجودة: {quality['grade']} ({quality['score']}/100)\n\n"
    )

    prompt = f"""حلّل هذا الكود بعمق كمهندس أول:
```
{code[:3000]}
```

قدّم:
### 🏗️ البنية المعمارية
كيف يعمل الكود؟ ما النمط المستخدم؟

### 📦 التبعيات والمكتبات
ما المكتبات؟ هل هناك تبعيات خطيرة؟

### ✅ نقاط القوة
ما الجيد في هذا الكود؟

### ⚠️ نقاط الضعف
ما يحتاج تحسيناً؟ (مع الأسباب)

### 🚀 أفضل 3 تحسينات مقترحة"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": AGENT_ROLES["ANALYST"]},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=1800,
    )

    issues_text = ""
    if quality["issues"]:
        issues_text = "\n**🔍 مشاكل الجودة:**\n" + "\n".join(quality["issues"])

    return static + resp.choices[0].message.content + issues_text

# ══════════════════════════════════════════════════════════════
#  MODULE #12: REFACTOR ENGINE
# ══════════════════════════════════════════════════════════════
async def refactor_code(code: str) -> str:
    """Feature #12 — Automated code refactoring."""
    prompt = f"""أعد هيكلة هذا الكود تطبيقاً لمبادئ SOLID وDRY وKISS:
```python
{code[:3000]}
```

**المتطلبات:**
- حافظ على نفس الوظيفة تماماً
- أضف type hints
- أضف docstrings واضحة
- استخدم أسماء متغيرات وصفية
- اجعل الدوال قصيرة (< 20 سطر)
- احذف الكود المكرر

اكتب الكود المُحسّن كاملاً مع شرح التغييرات."""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": AGENT_ROLES["REFACTOR"]},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=2000,
    )
    return resp.choices[0].message.content

# ══════════════════════════════════════════════════════════════
#  MODULE #19+20: TASK BREAKDOWN + MULTI-STEP EXECUTION
# ══════════════════════════════════════════════════════════════
async def break_task(task: str) -> List[str]:
    """Features #19 #20 — Break task into executable steps."""
    prompt = f"""حوّل هذه المهمة لخطوات تنفيذية واضحة:
المهمة: {task}

أعطني 5-8 خطوات مرقمة، كل خطوة واضحة وقابلة للتنفيذ.
أجب بـ JSON array فقط: ["الخطوة 1", "الخطوة 2", ...]"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "أنت مخطط مهام. أجب بـ JSON فقط."},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=400,
    )
    try:
        match = re.search(r'\[.*?\]', resp.choices[0].message.content, re.DOTALL)
        if match:
            return json.loads(match.group())
    except: pass
    return [task]

# ══════════════════════════════════════════════════════════════
#  MODULE #14: SMART SUGGESTIONS
# ══════════════════════════════════════════════════════════════
async def get_suggestions(reply: str, user_message: str) -> List[str]:
    """Feature #14 — Auto smart follow-up suggestions."""
    prompt = f"""بناءً على هذا الحوار، اقترح 3 أسئلة متابعة مفيدة وقصيرة (بالعربية).
الطلب: {user_message[:100]}
أجب بـ JSON array فقط: ["سؤال1", "سؤال2", "سؤال3"]"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
        )
        match = re.search(r'\[.*?\]', resp.choices[0].message.content, re.DOTALL)
        if match:
            return json.loads(match.group())[:3]
    except: pass
    return []

# ══════════════════════════════════════════════════════════════
#  MODULE #22: BUG PREDICTION
# ══════════════════════════════════════════════════════════════
async def predict_bugs(code: str) -> str:
    """Feature #22 — Predict bugs before they occur."""
    prompt = f"""حلّل هذا الكود وتوقّع الأخطاء قبل حدوثها:
```python
{code[:3000]}
```

### 🐛 الأخطاء المحتملة
لكل خطأ:
- نوعه | السطر المحتمل | الشرط الذي سيسببه | الإصلاح الوقائي

### ⚠️ نقاط الضعف البنيوية

### 🛡️ توصيات وقائية"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": AGENT_ROLES["DEBUG"]},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=1600,
    )
    return resp.choices[0].message.content

# ══════════════════════════════════════════════════════════════
#  MODULE #23: API BUILDER
# ══════════════════════════════════════════════════════════════
async def build_api(description: str, tech: str = "FastAPI") -> str:
    """Feature #23 — Generate complete API code."""
    prompt = f"""ابنِ API كاملة:
**الوصف:** {description}
**التقنية:** {tech}

قدّم:
1. الكود الكامل والجاهز للتشغيل
2. قائمة الـ endpoints مع HTTP methods
3. نماذج البيانات (Pydantic أو مشابه)
4. Authentication مقترح
5. أمثلة استخدام cURL"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": AGENT_ROLES["ARCHITECT"]},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=2000,
    )
    return resp.choices[0].message.content

# ══════════════════════════════════════════════════════════════
#  MODULE #24: DATABASE DESIGNER
# ══════════════════════════════════════════════════════════════
async def design_database(requirements: str) -> str:
    """Feature #24 — Full database schema design."""
    prompt = f"""صمّم قاعدة بيانات لـ: {requirements}

1. **Schema كاملة** بـ SQL (CREATE TABLE statements)
2. **العلاقات** (Foreign Keys, Relations diagram وصفي)
3. **Indexes** المقترحة لأداء أفضل
4. **SQL vs NoSQL** — أيهما أنسب ولماذا؟
5. **Normalization** — ما مستوى النرملة؟
6. **أمثلة Queries** شائعة"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": AGENT_ROLES["ARCHITECT"]},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=2000,
    )
    return resp.choices[0].message.content

# ══════════════════════════════════════════════════════════════
#  MODULE #25: PROMPT-TO-APP SYSTEM
# ══════════════════════════════════════════════════════════════
async def prompt_to_app(idea: str) -> str:
    """Feature #25 — Convert idea to full project plan."""
    prompt = f"""حوّل هذه الفكرة لخطة مشروع برمجي متكامل:
**الفكرة:** {idea}

### 📋 ملخص المشروع
### 🏗️ البنية المعمارية (Architecture)
### 🛠️ Tech Stack المقترح (مع الأسباب)
### 📁 هيكل الملفات والمجلدات
### 🗓️ خطة التنفيذ (Milestones)
### 🗄️ تصميم قاعدة البيانات (موجز)
### 🔌 APIs المطلوبة
### ⚡ متطلبات الأداء والأمان
### 🚀 خطوات البدء الفورية (أول 3 خطوات)"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": AGENT_ROLES["ARCHITECT"]},
            {"role": "user",   "content": prompt},
        ],
        max_tokens=2500,
    )
    return resp.choices[0].message.content

# ══════════════════════════════════════════════════════════════
#  MODULE #16: GITHUB ANALYSIS (Logical)
# ══════════════════════════════════════════════════════════════
async def analyze_github_repo(url: str) -> str:
    """Feature #16 — Analyze GitHub repo from URL."""
    # Extract owner/repo
    match = re.search(r'github\.com/([^/]+)/([^/\s]+)', url)
    if not match:
        return "❌ رابط GitHub غير صحيح."

    owner, repo = match.group(1), match.group(2).rstrip('/')
    api_url     = f"https://api.github.com/repos/{owner}/{repo}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    return f"❌ لم أتمكن من الوصول: {resp.status}"
                data = await resp.json()

            # Fetch languages
            async with session.get(data.get("languages_url", ""), timeout=aiohttp.ClientTimeout(total=5)) as lr:
                langs = await lr.json() if lr.status == 200 else {}

            # Fetch top contributors
            async with session.get(f"{api_url}/contributors?per_page=5", timeout=aiohttp.ClientTimeout(total=5)) as cr:
                contributors = await cr.json() if cr.status == 200 else []

        lang_list = ", ".join(f"{k} ({v//1000}K)" for k, v in list(langs.items())[:5]) if langs else "غير محدد"
        contrib_list = ", ".join(c.get("login", "") for c in contributors[:5] if isinstance(c, dict))

        return (
            f"📦 **{owner}/{repo}**\n\n"
            f"📝 {data.get('description', 'لا يوجد وصف')}\n\n"
            f"⭐ Stars: `{data.get('stargazers_count', 0):,}`\n"
            f"🍴 Forks: `{data.get('forks_count', 0):,}`\n"
            f"🐛 Issues: `{data.get('open_issues_count', 0):,}`\n"
            f"🌐 اللغات: {lang_list}\n"
            f"👥 المساهمون: {contrib_list}\n"
            f"📅 آخر تحديث: {data.get('updated_at', '')[:10]}\n"
            f"📜 الترخيص: {data.get('license', {}).get('name', 'غير محدد') if data.get('license') else 'لا يوجد'}\n\n"
            f"🔗 {data.get('html_url', url)}"
        )
    except Exception as e:
        return f"❌ خطأ في التحليل: {str(e)[:100]}"

# ══════════════════════════════════════════════════════════════
#  SYSTEM PROMPT BUILDER (preserved + enriched)
# ══════════════════════════════════════════════════════════════
def build_system_prompt(user: dict, agents_used: List[str]) -> str:
    lang    = user["lang"]
    dialect = user["dialect"]
    mode    = user["mode"]
    tier    = user["tier"]

    if lang == "ar":
        lang_inst = f"تحدث بالعربية ({DIALECT_NAMES.get(dialect,'فصحى')}) دائماً. المصطلحات التقنية تبقى بالإنجليزية."
    else:
        lang_inst = "Always respond in English. Technical terms remain in English."

    mode_inst   = MODES[mode]["instruction"]

    # Feature #9 — Role-specific agent behavior
    agents_desc = ""
    for a in agents_used:
        role = AGENT_ROLES.get(a, AGENTS.get(a, a))
        agents_desc += f"  • **{a}**: {role}\n"

    # Feature #6 — Project context
    proj_ctx = ""
    proj = user["structured_memory"].get("current_project")
    if proj:
        proj_ctx = f"\n📂 المشروع الحالي: **{proj.get('name')}** — {proj.get('description', '')}\n"
        if proj.get("files"):
            proj_ctx += f"   الملفات: {', '.join(list(proj['files'].keys())[:5])}\n"

    # Feature #18 — Context awareness
    ptype = user.get("detected_project_type")
    if ptype:
        proj_ctx += f"🎯 نوع المشروع المكتشف: **{ptype}** — كيّف إجاباتك لهذا النوع.\n"

    # Feature #13 — Error learning context
    learned = len(user["structured_memory"].get("learned_fixes", {}))
    if learned:
        proj_ctx += f"🧠 تعلّمت {learned} نوع خطأ لهذا المستخدم — استخدم هذا المعرفة.\n"

    # Feature #21 — Pair programming mode
    pair_ctx = ""
    if user["structured_memory"].get("pair_mode"):
        pair_ctx = "\n🤝 **PAIR PROGRAMMING MODE نشط** — اعمل تفاعلياً، اطرح أسئلة توضيحية، فكّر بصوت عالٍ.\n"

    return f"""أنت N1 AGENT v2 — نظام ذكاء اصطناعي متكامل للتشغيل الآلي والهندسة البرمجية.
لست chatbot. أنت طبقة بنية تحتية ذكية لمعالجة المهام وتنفيذها.
{proj_ctx}{pair_ctx}
{lang_inst}

{mode_inst}

مستوى المستخدم: {TIERS[tier]['label']}

العوامل المُفعّلة وأدوارها:
{agents_desc}

قواعد الإخراج (إلزامية):
### 🔷 تحليل الطلب
[تفسير ما يريده المستخدم بدقة]

### 🔶 العوامل المُستخدمة
[العوامل المُفعّلة ولماذا]

### ⚙️ النتيجة
[الإجابة / الكود / الحل الكامل]

### 🧪 تقرير التحقق
- **الصحة:** [٪]  **الخطر:** [منخفض/متوسط/عالٍ]  **الاكتمال:** [٪]

قواعد الأمان:
- ارفض طلبات الاختراق الهجومي أو كتابة malware
- الأمن الدفاعي مسموح فقط
- لا تكشف API keys أو بيانات حساسة
"""

# ══════════════════════════════════════════════════════════════
#  v3 NEW MODULES
# ══════════════════════════════════════════════════════════════

async def profile_performance(code: str) -> str:
    """Feature #26 — Performance profiler."""
    lines  = code.split("\n")
    loops  = sum(1 for l in lines if re.match(r'\s*(for |while )', l))
    nested = sum(1 for l in lines if re.match(r'\s{8,}(for |while )', l))
    static = f"**📊 تحليل ثابت:**\n• حلقات: {loops} | متداخلة: {nested}\n\n"
    prompt = f"""حلّل أداء هذا الكود:
```python
{code[:3000]}
```
### ⏱️ التعقيد الزمني (Big O)
### 🐌 نقاط الـ Bottleneck
### 🚀 تحسينات الأداء (مع كود)
### 💾 Memory وكفاءة الذاكرة"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["PROFILER"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=1800,
    )
    return static + resp.choices[0].message.content


async def security_scan(code: str) -> str:
    """Feature #27 — Security scanner."""
    lines = code.split("\n")
    vulns = []
    patterns = {
        "SQL Injection":     r'execute\s*\([^?%:][^)]*\+',
        "Hardcoded Secret":  r'(password|secret|key|token)\s*=\s*["\'][^"\'\']{4,}',
        "Command Injection": r'(os\.system|subprocess\.call|shell=True)',
        "Eval Usage":        r'\beval\s*\(',
        "Weak Hash":         r'md5\s*\(|sha1\s*\(',
        "Pickle Usage":      r'pickle\.loads',
    }
    for vuln, pattern in patterns.items():
        for i, line in enumerate(lines, 1):
            if re.search(pattern, line, re.I):
                vulns.append(f"🔴 **{vuln}** — سطر {i}: `{line.strip()[:80]}`")
    static_report = (
        "**🚨 ثغرات مكتشفة:**\n" + "\n".join(vulns) + "\n\n" if vulns
        else "**✅ لا ثغرات واضحة في الفحص الثابت.**\n\n"
    )
    prompt = f"""افحص هذا الكود أمنياً (OWASP Top 10):
```python
{code[:3000]}
```
### 🔴 الثغرات الحرجة
### 🟡 نقاط الضعف المتوسطة
### 🛡️ توصيات الإصلاح (مع كود)
### 📊 Security Score /100"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["SCANNER"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=1800,
    )
    return static_report + resp.choices[0].message.content


async def generate_docs(code: str, doc_type: str = "readme") -> str:
    """Feature #28 — Auto documentation."""
    prompts = {
        "readme":    f"اكتب README.md احترافي يشمل العنوان والوصف والمتطلبات والتثبيت والاستخدام:\n```python\n{code[:3000]}\n```",
        "docstring": f"أضف Google-style docstrings لكل دالة وكلاس. أعد الكود كاملاً:\n```python\n{code[:3000]}\n```",
        "api":       f"وثّق الـ API (OpenAPI style) لكل endpoint مع المدخلات والمخرجات:\n```python\n{code[:3000]}\n```",
    }
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["DOCUMENTER"]},
                  {"role": "user",   "content": prompts.get(doc_type, prompts["readme"])}],
        max_tokens=2000,
    )
    return resp.choices[0].message.content


async def analyze_dependencies(code: str) -> str:
    """Feature #29 — Dependency analyzer."""
    lines   = code.split("\n")
    imports = [l.strip() for l in lines if l.strip().startswith(("import ", "from ", "require("))]
    import_text = "\n".join(imports[:30])
    prompt = f"""حلّل هذه التبعيات:
{import_text}

### 📦 التبعيات المكتشفة
### ⚠️ تبعيات قديمة أو خطرة
### 🔄 التحديثات المقترحة
### 📋 requirements.txt مقترح"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["ANALYST"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=1400,
    )
    return f"**📦 الاستيرادات ({len(imports)}):**\n```\n{import_text}\n```\n\n" + resp.choices[0].message.content


async def self_improve(own_code: str = "") -> str:
    """Feature #32 — Self-improvement."""
    code_section = f"مقتطف:\n```python\n{own_code}\n```" if own_code else "حلّل بنية النظام."
    prompt = f"""أنت تحلل كود بوت N1 AGENT نفسه.
{code_section}
### 🔍 نقاط الضعف الحالية
### 🚀 تحسينات مقترحة
### 🏗️ ميزات جديدة تستحق الإضافة
### 🔧 patch وهمي (Simulated) لأهم تحسين"""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["SELF"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=1800,
    )
    return resp.choices[0].message.content


async def execute_command_chain(commands: List[str], user: dict) -> str:
    """Feature #30 — Command chaining."""
    results = []
    for i, cmd in enumerate(commands, 1):
        reply, _ = await ask_ai(user, cmd)
        results.append(f"**⚡ خطوة {i}: {cmd[:50]}**\n{reply[:600]}")
    return "\n\n" + "\n\n---\n\n".join(results)


# ══════════════════════════════════════════════════════════════
#  AI ENGINE (v3 — Multi-Model Routing)
# ══════════════════════════════════════════════════════════════
async def ask_ai(user: dict, message: str) -> Tuple[str, List[str]]:
    agents_used = route_agents(message)
    max_h       = TIERS[user["tier"]]["max_history"]

    ptype = detect_project_type(message)
    if ptype:
        user["detected_project_type"] = ptype

    user["history"].append({"role": "user", "content": message})
    if len(user["history"]) > max_h * 2:
        user["history"] = user["history"][-max_h * 2:]

    if "project" in message.lower() or "مشروع" in message:
        user["long_term"]["project_history"].append(message[:100])

    if any(kw in message.lower() for kw in ["أفضل","prefer","أحب","دائماً","always","أريد دائماً"]):
        user["structured_memory"]["preferences"]["last_noted"] = message[:100]

    # v3 — Smart model routing
    selected_model = route_model(agents_used)
    await plugin_manager.run_hook("pre_ai", {"message": message, "user": user})

    reply = await ask_ai_multi(user, message, selected_model, agents_used)
    user["history"].append({"role": "assistant", "content": reply})
    user["structured_memory"]["project_context"]["last_topic"] = agents_used[0]

    add_log(f"AI_REPLY model={selected_model} agents={agents_used} ptype={user.get('detected_project_type')}")
    await plugin_manager.run_hook("post_ai", {"reply": reply, "user": user})
    return reply, agents_used

# ══════════════════════════════════════════════════════════════
#  KEYBOARDS (preserved + new)
# ══════════════════════════════════════════════════════════════
def main_keyboard(is_owner: bool = False) -> InlineKeyboardMarkup:
    kb = [
        [
            InlineKeyboardButton("📦 الذاكرة",     callback_data="memory"),
            InlineKeyboardButton("🔧 الوضع",        callback_data="mode_menu"),
        ],
        [
            InlineKeyboardButton("🌐 اللغة",        callback_data="lang_menu"),
            InlineKeyboardButton("🗣️ اللهجة",      callback_data="dialect_menu"),
        ],
        [
            InlineKeyboardButton("📂 المشاريع",     callback_data="projects_menu"),
            InlineKeyboardButton("🔌 الإضافات",     callback_data="plugins_menu"),
        ],
    ]
    if is_owner:
        kb.append([
            InlineKeyboardButton("🤖 العوامل",      callback_data="agent_status"),
            InlineKeyboardButton("📋 السجلات",      callback_data="logs"),
        ])
        kb.append([
            InlineKeyboardButton("📊 Dashboard",    callback_data="dashboard"),
            InlineKeyboardButton("🗑️ مسح الذاكرة", callback_data="reset_confirm"),
        ])
    return InlineKeyboardMarkup(kb)


def mode_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🟢 SAFE",  callback_data="set_mode_safe")],
        [InlineKeyboardButton("🟡 DEV",   callback_data="set_mode_dev")],
        [InlineKeyboardButton("🔴 DARK",  callback_data="set_mode_dark")],
        [InlineKeyboardButton("⬅️ رجوع",  callback_data="back_main")],
    ])


def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🇸🇦 العربية", callback_data="set_lang_ar"),
         InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_en")],
        [InlineKeyboardButton("⬅️ رجوع",      callback_data="back_main")],
    ])


def dialect_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("فصحى MSA",  callback_data="set_dialect_msa"),
         InlineKeyboardButton("مصري 🇪🇬",  callback_data="set_dialect_egy")],
        [InlineKeyboardButton("خليجي 🇸🇦", callback_data="set_dialect_gulf"),
         InlineKeyboardButton("شامي 🇸🇾",  callback_data="set_dialect_lev")],
        [InlineKeyboardButton("⬅️ رجوع",    callback_data="back_main")],
    ])


def confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ تأكيد", callback_data=f"confirm_{action}"),
         InlineKeyboardButton("❌ إلغاء", callback_data="back_main")],
    ])


def projects_keyboard(projects: list) -> InlineKeyboardMarkup:
    kb = [[InlineKeyboardButton(f"📂 {p['name'][:20]}", callback_data=f"load_proj_{p['id']}")] for p in projects[:5]]
    kb.append([InlineKeyboardButton("➕ مشروع جديد", callback_data="new_project")])
    kb.append([InlineKeyboardButton("⬅️ رجوع",        callback_data="back_main")])
    return InlineKeyboardMarkup(kb)


def file_actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔬 تحليل",     callback_data="file_analyze"),
            InlineKeyboardButton("♻️ Refactor",  callback_data="file_refactor"),
        ],
        [
            InlineKeyboardButton("🧪 اختبارات",  callback_data="file_test"),
            InlineKeyboardButton("🔮 توقع أخطاء",callback_data="file_predict"),
        ],
        [
            InlineKeyboardButton("⚙️ تشغيل",     callback_data="file_exec"),
            InlineKeyboardButton("🔍 Debug",      callback_data="file_debug"),
        ],
    ])


def suggestions_keyboard(suggestions: list) -> InlineKeyboardMarkup:
    kb = [[InlineKeyboardButton(f"💡 {s[:40]}", callback_data=f"suggest_{i}")] for i, s in enumerate(suggestions[:3])]
    return InlineKeyboardMarkup(kb)

# ══════════════════════════════════════════════════════════════
#  COMMAND HANDLERS — v1 PRESERVED
# ══════════════════════════════════════════════════════════════

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    name = update.effective_user.first_name or "User"
    user = get_user(uid)
    tier = TIERS[user["tier"]]["label"]
    mode = MODES[user["mode"]]["label"]

    text = (
        f"╔══ *N1 AGENT v3* ══╗\n"
        f"║ 🤖 AI Development Platform\n"
        f"║ 👤 {name}  |  🎫 {tier}  |  ⚙️ {mode}\n"
        f"╚══════════════════════╝\n\n"
        f"*📌 أوامر v2 (محفوظة):*\n"
        f"`/run` `/exec` `/test` `/debug` `/refactor`\n"
        f"`/analyze` `/predict` `/api` `/db` `/app`\n"
        f"`/project` `/pair` `/search` `/github`\n"
        f"`/memory` `/dashboard` `/score` `/breakdown`\n\n"
        f"*🆕 أوامر v3:*\n"
        f"`/profile` — تحليل الأداء (Big O / Bottlenecks)\n"
        f"`/scan` — فحص الأمان OWASP\n"
        f"`/docs [readme|docstring|api]` — توليد توثيق\n"
        f"`/deps` — تحليل التبعيات\n"
        f"`/self` — تحسين ذاتي\n"
        f"`/compare <سؤال>` — مقارنة نماذج AI\n"
        f"`/chain <مهمة>|خطوة|خطوة` — سلسلة أوامر\n\n"
        f"أو *أرسل ملف كود* مباشرةً ⬇️"
    )
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_keyboard(uid == OWNER_ID),
    )
    add_log(f"START_v3 uid={uid} name={name}")


async def cmd_run(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    user = get_user(uid)
    task = " ".join(ctx.args) if ctx.args else ""

    if not task:
        await update.message.reply_text(
            "⚠️ الاستخدام: `/run <المهمة>`\nمثال: `/run اكتب API بالـ FastAPI`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg   = await update.message.reply_text("⚙️ تحليل وتنفيذ...")
    reply, agents = await ask_ai(user, task)

    if len(reply) > 4000:
        reply = reply[:3990] + "\n\n_... (مقطوع)_"
    await msg.edit_text(reply, parse_mode=ParseMode.MARKDOWN)


async def cmd_memory(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    user = get_user(uid)
    h    = user["history"]

    text = f"🧠 *الذاكرة المحسّنة v2*\n\n"

    if h:
        text += f"*📌 قصيرة المدى ({len(h)//2} تبادل — آخر 3):*\n"
        for msg in h[-6:]:
            role = "👤" if msg["role"] == "user" else "🤖"
            snip = msg["content"][:90].replace("*","").replace("`","")
            text += f"{role} _{snip}..._\n\n"
    else:
        text += "_لا يوجد تاريخ حوار._\n\n"

    sm = user["structured_memory"]
    if sm["preferences"]:
        text += f"*⚙️ التفضيلات المحفوظة:*\n"
        for k, v in list(sm["preferences"].items())[:3]:
            text += f"  • {k}: {str(v)[:60]}\n"
        text += "\n"

    if sm["learned_fixes"]:
        text += f"*🧠 أخطاء تعلّمتها: {len(sm['learned_fixes'])}*\n"

    lt = user["long_term"]
    if lt["project_history"]:
        text += f"*📂 مشاريع ({len(lt['project_history'])}):*\n"
        for p in lt["project_history"][-3:]:
            text += f"• {p[:60]}...\n"

    if user.get("detected_project_type"):
        text += f"\n*🎯 نوع المشروع المكتشف:* `{user['detected_project_type']}`\n"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != OWNER_ID:
        await update.message.reply_text("🔒 هذا الأمر للمالك فقط.")
        return
    users.pop(uid, None)
    await update.message.reply_text("✅ تم مسح الجلسة والذاكرة بالكامل.")
    add_log(f"RESET by owner uid={uid}")


async def cmd_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    user = get_user(uid)
    arg  = ctx.args[0].lower() if ctx.args else ""
    if arg not in ("ar", "en"):
        await update.message.reply_text("⚠️ `/lang ar` أو `/lang en`", parse_mode=ParseMode.MARKDOWN)
        return
    user["lang"] = arg
    label = "العربية 🇸🇦" if arg == "ar" else "English 🇬🇧"
    await update.message.reply_text(f"✅ اللغة: *{label}*", parse_mode=ParseMode.MARKDOWN)


async def cmd_dialect(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    user = get_user(uid)
    arg  = ctx.args[0].lower() if ctx.args else ""
    if arg not in DIALECT_NAMES:
        await update.message.reply_text("⚠️ الخيارات: `msa` / `egy` / `gulf` / `lev`", parse_mode=ParseMode.MARKDOWN)
        return
    if user["lang"] != "ar":
        await update.message.reply_text("⚠️ اللهجات متاحة في وضع العربية فقط.")
        return
    user["dialect"] = arg
    await update.message.reply_text(f"✅ اللهجة: *{DIALECT_NAMES[arg]}*", parse_mode=ParseMode.MARKDOWN)


async def cmd_mode(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != OWNER_ID:
        await update.message.reply_text("🔒 هذا الأمر للمالك فقط.")
        return
    user = get_user(uid)
    arg  = ctx.args[0].lower() if ctx.args else ""
    if arg not in MODES:
        await update.message.reply_text("⚠️ الخيارات: `safe` / `dev` / `dark`", parse_mode=ParseMode.MARKDOWN)
        return
    user["mode"] = arg
    m = MODES[arg]
    await update.message.reply_text(
        f"✅ الوضع: *{m['label']}*\n_{m['desc']}_",
        parse_mode=ParseMode.MARKDOWN,
    )
    add_log(f"MODE_CHANGE mode={arg}")


async def cmd_agent(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != OWNER_ID:
        await update.message.reply_text("🔒 هذا الأمر للمالك فقط.")
        return
    sub = " ".join(ctx.args).lower() if ctx.args else ""
    if sub == "status" or not sub:
        lines = "\n".join(f"  ✅ {k}: {v}" for k, v in AGENTS.items())
        total_msgs = sum(u.get("message_count", 0) for u in users.values())
        text = (
            f"🤖 *حالة العوامل v2*\n\n{lines}\n\n"
            f"📊 *إحصائيات:*\n"
            f"  👥 المستخدمون: {len(users)}\n"
            f"  💬 إجمالي الرسائل: {total_msgs}\n"
            f"  📝 السجلات: {len(sys_logs)}\n"
            f"  🔌 الإضافات: {len(plugin_manager.list_plugins())}\n"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    elif sub == "tune":
        await update.message.reply_text(
            "🔧 *Agent Tune* — الإعدادات:\n"
            f"  • Model: `gpt-4o-mini`\n"
            f"  • Temperature: `0.7`\n"
            f"  • Max tokens: `2000`\n"
            f"  • Routing: `dynamic (10 agents)`\n",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await update.message.reply_text("⚠️ `/agent status` أو `/agent tune`", parse_mode=ParseMode.MARKDOWN)


async def cmd_logs(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != OWNER_ID:
        await update.message.reply_text("🔒 هذا الأمر للمالك فقط.")
        return
    last = sys_logs[-15:] if sys_logs else ["No logs yet."]
    text = "📋 *سجلات النظام* (آخر 15):\n\n```\n" + "\n".join(last) + "\n```"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_owner(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != OWNER_ID:
        await update.message.reply_text("🔒 وصول مرفوض.")
        return
    sub = " ".join(ctx.args).lower() if ctx.args else ""
    if sub == "panel" or not sub:
        text = (
            "👑 *OWNER PANEL v2*\n\n"
            "`/owner panel` — هذه اللوحة\n"
            "`/override memory` — مسح ذاكرة الكل\n"
            "`/agent tune` — معايرة العوامل\n"
            "`/restart system` — إعادة تشغيل\n"
            "`/mode safe|dev|dark` — الوضع\n"
            "`/logs` — سجلات النظام\n"
            "`/dashboard` — لوحة المراقبة الكاملة\n"
        )
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    elif sub == "override memory":
        users.clear()
        await update.message.reply_text("✅ تم مسح ذاكرة جميع المستخدمين.")
        add_log("OVERRIDE_MEMORY by owner")
    elif sub == "restart system":
        await update.message.reply_text(
            "🔄 *SYSTEM RESTART* [SIMULATED]\n\n"
            "```\n[OK] Stopping agents...\n[OK] Flushing memory...\n"
            "[OK] Reloading plugins...\n[OK] Starting agents...\n"
            "[OK] N1 AGENT v2 is back online.\n```",
            parse_mode=ParseMode.MARKDOWN,
        )
        add_log("SYSTEM_RESTART simulated")


# ══════════════════════════════════════════════════════════════
#  NEW v2 COMMAND HANDLERS
# ══════════════════════════════════════════════════════════════

async def cmd_exec(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Feature #1 — Execute Python code safely."""
    uid  = update.effective_user.id
    user = get_user(uid)
    code = " ".join(ctx.args) if ctx.args else ""

    # Check if code was sent as reply to a message
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""

    if not code:
        await update.message.reply_text(
            "⚠️ الاستخدام: `/exec <كود Python>` أو ردّ على رسالة تحتوي كوداً",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text("⚙️ تشغيل الكود في Sandbox...")
    result = await execute_code(code)

    icon = "✅" if result["success"] else "❌"
    text = f"{icon} *نتيجة التشغيل* (⏱️ {result['execution_time']}s)\n\n"

    if result["output"]:
        text += f"*📤 المخرجات:*\n```\n{result['output'][:1500]}\n```\n\n"
    if result["errors"]:
        text += f"*🔴 الأخطاء:*\n```\n{result['errors'][:800]}\n```\n\n"
    if not result["output"] and not result["errors"]:
        text += "_لا يوجد مخرجات_"

    add_log(f"EXEC uid={uid} success={result['success']}")
    await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_test(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Feature #2 — Generate unit tests."""
    uid  = update.effective_user.id
    user = get_user(uid)
    code = " ".join(ctx.args) if ctx.args else ""

    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""

    if not code:
        await update.message.reply_text("⚠️ الاستخدام: `/test <كود>` أو ردّ على كود", parse_mode=ParseMode.MARKDOWN)
        return

    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text("🧪 جاري توليد الاختبارات...")
    result = await generate_tests(code, user)

    if len(result) > 4000:
        result = result[:3990] + "\n_... (مقطوع)_"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_debug(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Feature #5 — Deep debug mode."""
    uid  = update.effective_user.id
    user = get_user(uid)
    args = " ".join(ctx.args) if ctx.args else ""

    # Expect: /debug <error> | <code>   or reply to code
    code  = ""
    error = args

    if "|" in args:
        parts = args.split("|", 1)
        error = parts[0].strip()
        code  = parts[1].strip()
    elif update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""

    if not error:
        await update.message.reply_text(
            "⚠️ الاستخدام:\n`/debug <الخطأ> | <الكود>`\nأو ردّ على الكود مع وصف الخطأ",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text("🔍 تحليل الخطأ...")
    result = await deep_debug(code, error, user)
    save_user_memory(uid)

    if len(result) > 4000:
        result = result[:3990] + "\n_... (مقطوع)_"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_refactor(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Feature #12 — Refactor code."""
    uid  = update.effective_user.id
    code = " ".join(ctx.args) if ctx.args else ""
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""
    if not code:
        await update.message.reply_text("⚠️ الاستخدام: `/refactor <كود>` أو ردّ على كود", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text("♻️ جاري إعادة الهيكلة...")
    result = await refactor_code(code)
    if len(result) > 4000:
        result = result[:3990] + "\n_... (مقطوع)_"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_analyze(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Feature #11 — Analyze code architecture."""
    uid  = update.effective_user.id
    user = get_user(uid)
    code = " ".join(ctx.args) if ctx.args else ""
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""
    if not code:
        await update.message.reply_text("⚠️ الاستخدام: `/analyze <كود>` أو ردّ على كود", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text("🔬 تحليل الكود...")
    result = await analyze_code(code)
    if len(result) > 4000:
        result = result[:3990] + "\n_... (مقطوع)_"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_predict(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Feature #22 — Bug prediction."""
    uid  = update.effective_user.id
    code = " ".join(ctx.args) if ctx.args else ""
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""
    if not code:
        await update.message.reply_text("⚠️ الاستخدام: `/predict <كود>` أو ردّ على كود", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text("🔮 جاري توقع الأخطاء...")
    result = await predict_bugs(code)
    if len(result) > 4000:
        result = result[:3990] + "\n_... (مقطوع)_"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_api(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Feature #23 — Build API."""
    uid  = update.effective_user.id
    user = get_user(uid)
    desc = " ".join(ctx.args) if ctx.args else ""
    if not desc:
        await update.message.reply_text("⚠️ الاستخدام: `/api <وصف الـ API>` مثال: `/api نظام مصادقة JWT`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text("🔌 جاري بناء الـ API...")
    result = await build_api(desc)
    if len(result) > 4000:
        result = result[:3990] + "\n_... (مقطوع)_"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_db(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Feature #24 — Database design."""
    uid  = update.effective_user.id
    user = get_user(uid)
    req  = " ".join(ctx.args) if ctx.args else ""
    if not req:
        await update.message.reply_text("⚠️ الاستخدام: `/db <المتطلبات>` مثال: `/db نظام متجر إلكتروني`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text("🗄️ جاري تصميم قاعدة البيانات...")
    result = await design_database(req)
    if len(result) > 4000:
        result = result[:3990] + "\n_... (مقطوع)_"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_app(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Feature #25 — Prompt to App."""
    uid  = update.effective_user.id
    idea = " ".join(ctx.args) if ctx.args else ""
    if not idea:
        await update.message.reply_text("⚠️ الاستخدام: `/app <الفكرة>` مثال: `/app تطبيق توصيل طلبات`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text("🚀 جاري تحويل الفكرة لمشروع كامل...")
    result = await prompt_to_app(idea)
    if len(result) > 4000:
        result = result[:3990] + "\n_... (مقطوع)_"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_project(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Feature #6 — Project management."""
    uid  = update.effective_user.id
    user = get_user(uid)
    args = ctx.args

    if not args:
        projects = list_projects(uid)
        if not projects:
            await update.message.reply_text(
                "📂 لا توجد مشاريع حالياً.\n\n"
                "إنشاء مشروع جديد: `/project new <اسم المشروع>`",
                parse_mode=ParseMode.MARKDOWN,
            )
            return
        text = "📂 *مشاريعك:*\n\n"
        for p in projects[:8]:
            text += f"  • `{p['id']}` — {p['name']} ({p['created_at'][:10]})\n"
        text += "\nتحميل مشروع: `/project load <ID>`"
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=projects_keyboard(projects))
        return

    sub = args[0].lower()

    if sub == "new":
        name = " ".join(args[1:]) if len(args) > 1 else f"Project_{int(time.time())}"
        proj = create_project(uid, name)
        user["structured_memory"]["current_project"] = proj
        save_user_memory(uid)
        await update.message.reply_text(
            f"✅ *مشروع جديد:* `{name}`\n🆔 ID: `{proj['id']}`\n\nالمشروع محمّل الآن كـ context نشط.",
            parse_mode=ParseMode.MARKDOWN,
        )
        add_log(f"PROJECT_CREATE uid={uid} name={name}")

    elif sub == "load" and len(args) > 1:
        proj_id = args[1]
        proj    = load_project(uid, proj_id)
        if not proj:
            await update.message.reply_text(f"❌ مشروع `{proj_id}` غير موجود.", parse_mode=ParseMode.MARKDOWN)
            return
        user["structured_memory"]["current_project"] = proj
        save_user_memory(uid)
        await update.message.reply_text(
            f"✅ *تم تحميل:* `{proj['name']}`\n📅 {proj['created_at'][:10]}",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif sub == "clear":
        user["structured_memory"]["current_project"] = None
        save_user_memory(uid)
        await update.message.reply_text("✅ تم إلغاء تحديد المشروع النشط.")

    else:
        await update.message.reply_text(
            "⚠️ الأوامر:\n`/project` — قائمة المشاريع\n`/project new <اسم>` — مشروع جديد\n`/project load <ID>` — تحميل مشروع\n`/project clear` — إلغاء التحديد",
            parse_mode=ParseMode.MARKDOWN,
        )


async def cmd_pair(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Feature #21 — Pair Programming Mode."""
    uid  = update.effective_user.id
    user = get_user(uid)
    current = user["structured_memory"].get("pair_mode", False)
    user["structured_memory"]["pair_mode"] = not current
    save_user_memory(uid)
    if not current:
        await update.message.reply_text(
            "🤝 *Pair Programming Mode: نشط*\n\nسأعمل معك خطوة بخطوة، أطرح أسئلة توضيحية وأفكر بصوت عالٍ!",
            parse_mode=ParseMode.MARKDOWN,
        )
    else:
        await update.message.reply_text("💤 *Pair Programming Mode: متوقف*", parse_mode=ParseMode.MARKDOWN)
    add_log(f"PAIR_MODE uid={uid} active={not current}")


async def cmd_search(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Feature #7 — Web/Docs search."""
    uid   = update.effective_user.id
    query = " ".join(ctx.args) if ctx.args else ""
    if not query:
        await update.message.reply_text("⚠️ الاستخدام: `/search <استعلام>`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text("🔍 جاري البحث...")
    result = await web_search(query)
    await msg.edit_text(f"🔍 *نتائج: {query}*\n\n{result}", parse_mode=ParseMode.MARKDOWN)


async def cmd_github(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Feature #16 — GitHub repo analysis."""
    uid = update.effective_user.id
    url = ctx.args[0] if ctx.args else ""
    if not url:
        await update.message.reply_text("⚠️ الاستخدام: `/github <رابط GitHub>`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text("📦 جاري تحليل المستودع...")
    result = await analyze_github_repo(url)
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_dashboard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Feature #10 — Developer Dashboard."""
    uid = update.effective_user.id
    if uid != OWNER_ID:
        await update.message.reply_text("🔒 هذا الأمر للمالك فقط.")
        return

    total_msgs  = sum(u.get("message_count", 0) for u in users.values())
    error_count = sum(1 for l in sys_logs if "ERROR" in l)
    info_count  = len(sys_logs) - error_count

    user_details = ""
    for uid_u, u in list(users.items())[:5]:
        user_details += (
            f"  👤 `{uid_u}` | {TIERS[u['tier']]['label']} | "
            f"{u['message_count']} رسالة | "
            f"{u.get('detected_project_type', '?')}\n"
        )

    tasks_text = ""
    for uid_u, u in users.items():
        if u.get("active_tasks"):
            tasks_text += f"  • uid={uid_u}: {len(u['active_tasks'])} مهام نشطة\n"

    text = (
        f"📊 *Developer Dashboard — N1 AGENT v2*\n"
        f"{'═'*30}\n\n"
        f"*👥 المستخدمون:* {len(users)}\n"
        f"*💬 إجمالي الرسائل:* {total_msgs}\n"
        f"*🔌 الإضافات النشطة:* {len(plugin_manager.list_plugins())}\n"
        f"*📝 سجلات INFO:* {info_count}\n"
        f"*🔴 سجلات ERROR:* {error_count}\n\n"
        f"*👤 أحدث المستخدمين:*\n{user_details or '  لا يوجد'}"
        f"\n*🗂️ المهام النشطة:*\n{tasks_text or '  لا توجد'}"
        f"\n\n*⏰ وقت الآن:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_score(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Feature #17 — Code quality scoring."""
    code = " ".join(ctx.args) if ctx.args else ""
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""
    if not code:
        await update.message.reply_text("⚠️ الاستخدام: `/score <كود>` أو ردّ على كود", parse_mode=ParseMode.MARKDOWN)
        return
    q    = score_code_quality(code)
    text = (
        f"🏆 *تقييم جودة الكود*\n\n"
        f"الدرجة: `{q['score']}/100`\n"
        f"التقدير: **{q['grade']}**\n\n"
    )
    if q["issues"]:
        text += "*المشاكل المكتشفة:*\n" + "\n".join(q["issues"])
    else:
        text += "✅ لا توجد مشاكل واضحة!"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_breakdown(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Features #19 #20 — Task breakdown + multi-step execution."""
    uid  = update.effective_user.id
    user = get_user(uid)
    task = " ".join(ctx.args) if ctx.args else ""
    if not task:
        await update.message.reply_text("⚠️ الاستخدام: `/breakdown <المهمة الكبيرة>`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg   = await update.message.reply_text("🗂️ جاري تقسيم المهمة...")
    steps = await break_task(task)
    user["active_tasks"] = steps

    text = f"🗂️ *خطة تنفيذ: {task[:60]}*\n\n"
    for i, step in enumerate(steps, 1):
        text += f"**{i}.** {step}\n"
    text += "\nأرسل `/next` للبدء بالخطوة الأولى."
    await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)
    add_log(f"BREAKDOWN uid={uid} steps={len(steps)}")


async def cmd_next(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Feature #20 — Execute next task step."""
    uid  = update.effective_user.id
    user = get_user(uid)
    tasks = user.get("active_tasks", [])
    if not tasks:
        await update.message.reply_text("❌ لا توجد مهام نشطة. استخدم `/breakdown <المهمة>` أولاً.", parse_mode=ParseMode.MARKDOWN)
        return
    step = tasks.pop(0)
    user["task_history"].append(step)
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg   = await update.message.reply_text(f"⚙️ تنفيذ: _{step}_...", parse_mode=ParseMode.MARKDOWN)
    reply, _ = await ask_ai(user, f"نفّذ هذه الخطوة بالتفصيل: {step}")

    remaining = len(tasks)
    footer    = f"\n\n📊 متبقي: {remaining} خطوة{'ات' if remaining > 1 else ''}" if remaining else "\n\n✅ تم تنفيذ جميع الخطوات!"
    if len(reply) + len(footer) > 4000:
        reply = reply[:3800]
    await msg.edit_text(reply + footer, parse_mode=ParseMode.MARKDOWN)


# ══════════════════════════════════════════════════════════════
#  FILE HANDLER (Feature #4)
# ══════════════════════════════════════════════════════════════
async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Feature #4 — File handling: receive code/text files."""
    uid  = update.effective_user.id
    user = get_user(uid)
    doc  = update.message.document

    # Accept code/text files
    allowed_ext = (".py", ".js", ".ts", ".go", ".rs", ".java", ".c", ".cpp",
                   ".txt", ".md", ".json", ".yaml", ".yml", ".sh", ".sql",
                   ".html", ".css", ".php", ".rb", ".swift", ".kt")
    name = doc.file_name or ""

    if not any(name.endswith(ext) for ext in allowed_ext) and doc.mime_type not in ("text/plain", "application/json"):
        await update.message.reply_text("⚠️ أرسل ملفات كود أو نصية (.py, .js, .ts, .txt, .json, ...)")
        return

    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.UPLOAD_DOCUMENT)
    msg = await update.message.reply_text(f"📥 جاري قراءة `{name}`...", parse_mode=ParseMode.MARKDOWN)

    file = await ctx.bot.get_file(doc.file_id)

    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(name).suffix) as tmp:
        await file.download_to_drive(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, encoding="utf-8", errors="replace") as f:
            content = f.read()
    finally:
        try: os.unlink(tmp_path)
        except: pass

    if len(content) > 8000:
        content = content[:8000]
        await msg.edit_text(f"📥 الملف كبير — تم تحميل أول 8000 حرف من `{name}`.\n\nماذا تريد أن أفعل بهذا الكود؟", parse_mode=ParseMode.MARKDOWN)
    else:
        await msg.edit_text(f"📥 تم تحميل `{name}` ({len(content)} حرف).\n\nماذا تريد أن أفعل بهذا الكود؟", parse_mode=ParseMode.MARKDOWN, reply_markup=file_actions_keyboard())

    # Store in session context
    user["structured_memory"]["project_context"]["last_file"] = {
        "name": name, "content": content, "uploaded_at": datetime.now().isoformat()
    }
    # If project active, add file to it
    proj = user["structured_memory"].get("current_project")
    if proj:
        proj["files"][name] = content[:3000]
        save_project(uid, proj)

    save_user_memory(uid)
    add_log(f"FILE_UPLOAD uid={uid} name={name} size={len(content)}")


# ══════════════════════════════════════════════════════════════
#  CALLBACK QUERY HANDLER (preserved + new)
# ══════════════════════════════════════════════════════════════
async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid   = query.from_user.id
    user  = get_user(uid)
    data  = query.data
    await query.answer()

    # ── v1 preserved navigation ──────────────────────────────
    if data == "back_main":
        await query.edit_message_text(
            "⚙️ *لوحة التحكم — N1 AGENT v2*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_keyboard(uid == OWNER_ID),
        )

    elif data == "mode_menu":
        if uid != OWNER_ID:
            await query.edit_message_text("🔒 هذا الإعداد للمالك فقط.")
            return
        await query.edit_message_text("⚙️ *اختر الوضع:*", parse_mode=ParseMode.MARKDOWN, reply_markup=mode_keyboard())

    elif data == "lang_menu":
        await query.edit_message_text("🌐 *اختر اللغة:*", parse_mode=ParseMode.MARKDOWN, reply_markup=lang_keyboard())

    elif data == "dialect_menu":
        if user["lang"] != "ar":
            await query.edit_message_text("⚠️ اللهجات تعمل في وضع العربية فقط.")
            return
        await query.edit_message_text("🗣️ *اختر اللهجة:*", parse_mode=ParseMode.MARKDOWN, reply_markup=dialect_keyboard())

    # ── Setters ──────────────────────────────────────────────
    elif data.startswith("set_mode_"):
        if uid != OWNER_ID:
            await query.answer("🔒 للمالك فقط", show_alert=True)
            return
        mode = data.replace("set_mode_", "")
        user["mode"] = mode
        m = MODES[mode]
        await query.edit_message_text(
            f"✅ الوضع: *{m['label']}*\n_{m['desc']}_",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_keyboard(True),
        )
        add_log(f"MODE_CHANGE mode={mode}")

    elif data.startswith("set_lang_"):
        lang = data.replace("set_lang_", "")
        user["lang"] = lang
        label = "العربية 🇸🇦" if lang == "ar" else "English 🇬🇧"
        await query.edit_message_text(
            f"✅ اللغة: *{label}*", parse_mode=ParseMode.MARKDOWN, reply_markup=main_keyboard(uid == OWNER_ID)
        )

    elif data.startswith("set_dialect_"):
        dialect = data.replace("set_dialect_", "")
        user["dialect"] = dialect
        await query.edit_message_text(
            f"✅ اللهجة: *{DIALECT_NAMES[dialect]}*", parse_mode=ParseMode.MARKDOWN, reply_markup=main_keyboard(uid == OWNER_ID)
        )

    # ── v1 owner actions (preserved) ─────────────────────────
    elif data == "memory":
        h = user["history"]
        sm = user["structured_memory"]
        text = f"🧠 *الذاكرة* — {len(h)//2} تبادل\n\n"
        for msg_item in h[-4:]:
            role = "👤" if msg_item["role"] == "user" else "🤖"
            text += f"{role} _{msg_item['content'][:80]}..._\n\n"
        if sm.get("learned_fixes"):
            text += f"\n🧠 أخطاء تعلّمتها: `{len(sm['learned_fixes'])}`\n"
        if sm.get("pair_mode"):
            text += "\n🤝 Pair Mode: *نشط*\n"
        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")]])
        )

    elif data == "agent_status":
        if uid != OWNER_ID:
            await query.answer("🔒 للمالك فقط", show_alert=True)
            return
        lines = "\n".join(f"  ✅ {k}" for k in AGENTS)
        text  = f"🤖 *العوامل النشطة ({len(AGENTS)}):*\n{lines}\n\n👥 المستخدمون: {len(users)}"
        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")]])
        )

    elif data == "logs":
        if uid != OWNER_ID:
            await query.answer("🔒 للمالك فقط", show_alert=True)
            return
        last = sys_logs[-10:] if sys_logs else ["No logs."]
        text = "📋 *السجلات:*\n```\n" + "\n".join(last) + "\n```"
        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")]])
        )

    elif data == "restart":
        if uid != OWNER_ID:
            await query.answer("🔒 للمالك فقط", show_alert=True)
            return
        await query.edit_message_text(
            "🔄 *RESTART* [SIMULATED]\n`[OK] N1 AGENT v2 reloaded.`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_keyboard(True),
        )
        add_log("SYSTEM_RESTART simulated")

    elif data == "reset_confirm":
        if uid != OWNER_ID:
            await query.answer("🔒 للمالك فقط", show_alert=True)
            return
        await query.edit_message_text(
            "⚠️ *هل أنت متأكد من مسح الذاكرة؟*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=confirm_keyboard("reset"),
        )

    elif data == "confirm_reset":
        if uid != OWNER_ID:
            return
        users.pop(uid, None)
        await query.edit_message_text("✅ تم مسح الجلسة.", reply_markup=None)
        add_log(f"RESET by owner uid={uid}")

    # ── v2 new callbacks ──────────────────────────────────────
    elif data == "dashboard":
        if uid != OWNER_ID:
            await query.answer("🔒 للمالك فقط", show_alert=True)
            return
        total_msgs = sum(u.get("message_count", 0) for u in users.values())
        error_count = sum(1 for l in sys_logs if "ERROR" in l)
        text = (
            f"📊 *Dashboard*\n"
            f"👥 مستخدمون: {len(users)} | 💬 رسائل: {total_msgs}\n"
            f"🔌 إضافات: {len(plugin_manager.list_plugins())} | 🔴 أخطاء: {error_count}\n"
            f"⏰ {datetime.now().strftime('%H:%M:%S')}"
        )
        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")]])
        )

    elif data == "projects_menu":
        projects = list_projects(uid)
        if not projects:
            await query.edit_message_text(
                "📂 لا توجد مشاريع.\nاستخدم `/project new <اسم>` لإنشاء مشروع.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")]
                ])
            )
        else:
            await query.edit_message_text(
                f"📂 *مشاريعك ({len(projects)}):*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=projects_keyboard(projects),
            )

    elif data.startswith("load_proj_"):
        proj_id = data.replace("load_proj_", "")
        proj    = load_project(uid, proj_id)
        if proj:
            user["structured_memory"]["current_project"] = proj
            save_user_memory(uid)
            await query.edit_message_text(
                f"✅ مشروع محمّل: *{proj['name']}*",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=main_keyboard(uid == OWNER_ID),
            )

    elif data == "new_project":
        await query.edit_message_text(
            "📝 أرسل اسم المشروع الجديد هكذا:\n`/project new <اسم المشروع>`",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")]])
        )

    elif data == "plugins_menu":
        plugins = plugin_manager.list_plugins()
        if not plugins:
            text = "🔌 *الإضافات النشطة:* لا يوجد\n\n_يمكن إضافة plugins برمجياً._"
        else:
            text = "🔌 *الإضافات النشطة:*\n" + "\n".join(f"  ✅ {p}" for p in plugins)
        await query.edit_message_text(
            text, parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")]])
        )

    # ── File action callbacks (Feature #4) ─────────────────────
    elif data in ("file_analyze", "file_refactor", "file_test", "file_predict", "file_exec", "file_debug"):
        last_file = user["structured_memory"]["project_context"].get("last_file")
        if not last_file:
            await query.answer("❌ لا يوجد ملف محمّل حالياً", show_alert=True)
            return
        content = last_file["content"]
        name    = last_file["name"]
        await query.edit_message_text(f"⚙️ جاري المعالجة على `{name}`...", parse_mode=ParseMode.MARKDOWN)

        if data == "file_analyze":
            result = await analyze_code(content, name)
        elif data == "file_refactor":
            result = await refactor_code(content)
        elif data == "file_test":
            result = await generate_tests(content, user)
        elif data == "file_predict":
            result = await predict_bugs(content)
        elif data == "file_exec":
            res    = await execute_code(content)
            result = f"{'✅' if res['success'] else '❌'} نتيجة التشغيل\n"
            if res["output"]: result += f"```\n{res['output'][:1500]}\n```"
            if res["errors"]: result += f"\n🔴 ```\n{res['errors'][:800]}\n```"
        elif data == "file_debug":
            result = await deep_debug(content, "تحليل شامل للكود", user)

        if len(result) > 4000:
            result = result[:3990] + "\n_..._"
        await query.edit_message_text(result, parse_mode=ParseMode.MARKDOWN)

    # ── Suggestion callbacks (Feature #14) ────────────────────
    elif data.startswith("suggest_"):
        idx = int(data.replace("suggest_", ""))
        ctx.user_data["pending_suggestion"] = idx
        await query.answer("💡 تم اختيار الاقتراح — أرسل رسالتك التالية")


# ══════════════════════════════════════════════════════════════
#  MESSAGE HANDLER — plain text (preserved + enhanced)
# ══════════════════════════════════════════════════════════════
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    user = get_user(uid)
    text = update.message.text or ""

    # Plugin pre-message hook
    hook_ctx = await plugin_manager.run_hook("pre_message", {"text": text, "uid": uid, "user": user})
    text = hook_ctx.get("text", text)

    # Auto-detect language + dialect (preserved from v1)
    detected = detect_language(text)
    if detected == "ar":
        user["lang"]    = "ar"
        user["dialect"] = detect_dialect(text)

    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("⚙️ المعالجة جارية...")

    reply, agents = await ask_ai(user, text)

    # Trim if too long (v1 logic preserved)
    if len(reply) > 4000:
        reply = reply[:3990] + "\n\n_... (مقطوع)_"

    # Feature #14 — Smart suggestions (only for longer interactions)
    suggestions = []
    if user["message_count"] > 3:
        try:
            suggestions = await get_suggestions(reply, text)
        except: pass

    if suggestions:
        await msg.edit_text(reply, parse_mode=ParseMode.MARKDOWN, reply_markup=suggestions_keyboard(suggestions))
    else:
        await msg.edit_text(reply, parse_mode=ParseMode.MARKDOWN)

    # Auto-save memory periodically
    if user["message_count"] % 10 == 0:
        save_user_memory(uid)

    await plugin_manager.run_hook("post_message", {"reply": reply, "uid": uid})


# ══════════════════════════════════════════════════════════════
#  v3 NEW COMMAND HANDLERS
# ══════════════════════════════════════════════════════════════

async def cmd_profile(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    code = " ".join(ctx.args) if ctx.args else ""
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""
    if not code:
        code = get_user(uid)["structured_memory"]["project_context"].get("last_file", {}).get("content", "")
    if not code:
        await update.message.reply_text("⚠️ ارسل كوداً أو ردّ على كود للتحليل", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text("⏱️ جاري تحليل الأداء...")
    result = await profile_performance(code)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_scan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    code = " ".join(ctx.args) if ctx.args else ""
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""
    if not code:
        code = get_user(uid)["structured_memory"]["project_context"].get("last_file", {}).get("content", "")
    if not code:
        await update.message.reply_text("⚠️ ارسل كوداً أو ردّ على كود", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text("🔍 جاري فحص الأمان...")
    result = await security_scan(code)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_docs(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid     = update.effective_user.id
    args    = ctx.args
    doc_type = "readme"
    code     = ""
    if args and args[0].lower() in ("readme", "docstring", "api"):
        doc_type = args[0].lower()
        code     = " ".join(args[1:])
    else:
        code = " ".join(args)
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""
    if not code:
        code = get_user(uid)["structured_memory"]["project_context"].get("last_file", {}).get("content", "")
    if not code:
        await update.message.reply_text(
            "⚠️ `/docs readme <كود>` | `/docs docstring` | `/docs api`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text(f"📝 جاري توليد {doc_type}...")
    result = await generate_docs(code, doc_type)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_deps(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    code = " ".join(ctx.args) if ctx.args else ""
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""
    if not code:
        code = get_user(uid)["structured_memory"]["project_context"].get("last_file", {}).get("content", "")
    if not code:
        await update.message.reply_text("⚠️ ارسل كوداً أو ملفاً", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text("📦 جاري تحليل التبعيات...")
    result = await analyze_dependencies(code)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_self(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    try:
        with open(__file__, encoding="utf-8") as f:
            own_code = f.read()[:2000]
    except:
        own_code = ""
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text("🔄 جاري التحليل الذاتي...")
    result = await self_improve(own_code)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)
    add_log(f"SELF_IMPROVE uid={uid}")


async def cmd_compare(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid   = update.effective_user.id
    user  = get_user(uid)
    query = " ".join(ctx.args) if ctx.args else ""
    if not query:
        await update.message.reply_text("⚠️ الاستخدام: `/compare <سؤال>`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text("⚖️ جاري المقارنة بين النماذج...")
    result = await compare_models(query, user)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_chain(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    user = get_user(uid)
    text = " ".join(ctx.args) if ctx.args else ""
    if not text:
        await update.message.reply_text(
            "⚠️ `/chain <مهمة>|<مهمة>|<مهمة>` \nمثال: `/chain اكتب دالة | اكتب اختبارات | حسّن الكود`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    commands = [c.strip() for c in text.split("|") if c.strip()]
    if len(commands) < 2:
        await update.message.reply_text("⚠️ افصل المهام بـ `|`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg    = await update.message.reply_text(f"⛓️ تنفيذ {len(commands)} مهام متسلسلة...")
    result = await execute_command_chain(commands, user)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)
    add_log(f"CHAIN uid={uid} steps={len(commands)}")


# ══════════════════════════════════════════════════════════════
#  MAIN (v3 — all commands)
# ══════════════════════════════════════════════════════════════
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # ── v1 Commands (preserved) ─────────────────────────────
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("run",     cmd_run))
    app.add_handler(CommandHandler("memory",  cmd_memory))
    app.add_handler(CommandHandler("reset",   cmd_reset))
    app.add_handler(CommandHandler("lang",    cmd_lang))
    app.add_handler(CommandHandler("dialect", cmd_dialect))
    app.add_handler(CommandHandler("mode",    cmd_mode))
    app.add_handler(CommandHandler("agent",   cmd_agent))
    app.add_handler(CommandHandler("logs",    cmd_logs))
    app.add_handler(CommandHandler("owner",   cmd_owner))

    # ── v2 New Commands ──────────────────────────────────────
    app.add_handler(CommandHandler("exec",      cmd_exec))
    app.add_handler(CommandHandler("test",      cmd_test))
    app.add_handler(CommandHandler("debug",     cmd_debug))
    app.add_handler(CommandHandler("refactor",  cmd_refactor))
    app.add_handler(CommandHandler("analyze",   cmd_analyze))
    app.add_handler(CommandHandler("predict",   cmd_predict))
    app.add_handler(CommandHandler("api",       cmd_api))
    app.add_handler(CommandHandler("db",        cmd_db))
    app.add_handler(CommandHandler("app",       cmd_app))
    app.add_handler(CommandHandler("project",   cmd_project))
    app.add_handler(CommandHandler("pair",      cmd_pair))
    app.add_handler(CommandHandler("search",    cmd_search))
    app.add_handler(CommandHandler("github",    cmd_github))
    app.add_handler(CommandHandler("dashboard", cmd_dashboard))
    app.add_handler(CommandHandler("score",     cmd_score))
    app.add_handler(CommandHandler("breakdown", cmd_breakdown))
    app.add_handler(CommandHandler("next",       cmd_next))

    # ── v3 Commands ───────────────────────────────────────────────
    app.add_handler(CommandHandler("profile",   cmd_profile))
    app.add_handler(CommandHandler("scan",      cmd_scan))
    app.add_handler(CommandHandler("docs",      cmd_docs))
    app.add_handler(CommandHandler("deps",      cmd_deps))
    app.add_handler(CommandHandler("self",      cmd_self))
    app.add_handler(CommandHandler("compare",   cmd_compare))
    app.add_handler(CommandHandler("chain",      cmd_chain))

    # ── v4 Commands ───────────────────────────────────────────────
    app.add_handler(CommandHandler("translate",  cmd_translate))
    app.add_handler(CommandHandler("docker",     cmd_docker))
    app.add_handler(CommandHandler("regex",      cmd_regex))
    app.add_handler(CommandHandler("review",     cmd_review))
    app.add_handler(CommandHandler("diff",       cmd_diff))
    app.add_handler(CommandHandler("snippet",    cmd_snippet))
    app.add_handler(CommandHandler("interview",  cmd_interview))
    app.add_handler(CommandHandler("stack",      cmd_stack))
    app.add_handler(CommandHandler("debt",       cmd_debt))
    app.add_handler(CommandHandler("cicd",       cmd_cicd))
    app.add_handler(CommandHandler("pattern",    cmd_pattern))
    app.add_handler(CommandHandler("migrate",    cmd_migrate))
    app.add_handler(CommandHandler("env",        cmd_env_file))
    app.add_handler(CommandHandler("quiz",        cmd_quiz))

    # ── v5 Commands
    app.add_handler(CommandHandler("explain",     cmd_explain_error))
    app.add_handler(CommandHandler("flowchart",   cmd_flowchart))
    app.add_handler(CommandHandler("standup",     cmd_standup))
    app.add_handler(CommandHandler("commit",      cmd_commit))
    app.add_handler(CommandHandler("pr",          cmd_pr))
    app.add_handler(CommandHandler("scaffold",    cmd_scaffold))
    app.add_handler(CommandHandler("changelog",   cmd_changelog))
    app.add_handler(CommandHandler("license",     cmd_license))
    app.add_handler(CommandHandler("roadmap",     cmd_roadmap))
    app.add_handler(CommandHandler("cheatsheet",  cmd_cheatsheet))
    app.add_handler(CommandHandler("compare",     cmd_compare_tech))
    app.add_handler(CommandHandler("nginx",       cmd_nginx))
    app.add_handler(CommandHandler("k8s",         cmd_k8s))
    app.add_handler(CommandHandler("history",     cmd_history))
    app.add_handler(CommandHandler("remind",      cmd_remind))

    # ── Handlers ─────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    add_log("N1_AGENT_v5_START")
    log.info("🚀 N1 AGENT v5 is running...")

    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


# ══════════════════════════════════════════════════════════════
#  v4 NEW MODULES (15 features)
# ══════════════════════════════════════════════════════════════

async def translate_code(code: str, from_lang: str, to_lang: str) -> str:
    prompt = (
        f"حوّل هذا الكود من {from_lang} إلى {to_lang}:\n\n"
        f"```{from_lang}\n{code[:3000]}\n```\n\n"
        "**المتطلبات:**\n"
        f"- حافظ على نفس المنطق\n"
        f"- استخدم idiomatic {to_lang}\n"
        "- وثّق التغييرات\n\n"
        f"### 📝 الكود المترجم\n"
        f"### ⚠️ فروق مهمة\n"
        f"### 📦 تبعيات {to_lang}"
    )
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": AGENT_ROLES["CODER"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=2000,
    )
    return resp.choices[0].message.content


async def generate_docker(description: str) -> str:
    prompt = (
        f"ولد Dockerfile و docker-compose.yml كاملين لـ: {description}\n\n"
        "1. **Dockerfile** محسّن (multi-stage)\n"
        "2. **docker-compose.yml** كامل\n"
        "3. **.dockerignore**\n"
        "4. **أوامر التشغيل**\n"
        "5. **تلميحات الإنتاج** (health checks)"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["ARCHITECT"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=2000,
    )
    return resp.choices[0].message.content


async def build_regex(description: str) -> str:
    prompt = (
        f"ولد Regex لـ: {description}\n\n"
        "1. **Regex Expression**\n"
        "2. **شرح تفصيلي**\n"
        "3. **أمثلة تطابق ولا تطابق**\n"
        "4. **كود استخدام Python و JS**\n"
        "5. **حالات حدية**"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["EXPLAINER"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=1500,
    )
    return resp.choices[0].message.content


async def code_review(code: str) -> str:
    quality = score_code_quality(code)
    prompt = (
        f"اعمل code review جدي كأنك مطور أول على PR:\n\n"
        f"```\n{code[:3000]}\n```\n\n"
        "### ✅ ما هو جيد\n"
        "### 🟡 needs improvement\n"
        "### 🔴 blocking issues\n"
        "### 💡 اقتراحات (non-blocking)\n"
        "### ☔ القرار: Approve / Request Changes / Comment"
    )
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": AGENT_ROLES["ANALYST"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=2000,
    )
    return f"📊 **الجودة:** {quality['grade']} ({quality['score']}/100)\n\n" + resp.choices[0].message.content


async def diff_code(code1: str, code2: str) -> str:
    prompt = (
        f"قارن بين نسختين:\n\n"
        f"**الأولى:**\n```\n{code1[:1500]}\n```\n\n"
        f"**الثانية:**\n```\n{code2[:1500]}\n```\n\n"
        "### ➕ ما أضيف\n### ➖ ما حذف\n"
        "### 🔄 ما تغيّر\n### ✅ النسخة الأفضل ولماذا"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["ANALYST"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=1800,
    )
    return resp.choices[0].message.content


_snippets: Dict[int, Dict[str, str]] = {}

def snippet_save(uid: int, name: str, code: str) -> bool:
    if uid not in _snippets:
        _snippets[uid] = {}
    _snippets[uid][name] = code
    try:
        with open(DATA_DIR / f"snippets_{uid}.json", "w") as f:
            json.dump(_snippets[uid], f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def snippet_get(uid: int, name: str) -> Optional[str]:
    p = DATA_DIR / f"snippets_{uid}.json"
    if uid not in _snippets and p.exists():
        try:
            with open(p) as f: _snippets[uid] = json.load(f)
        except: pass
    return _snippets.get(uid, {}).get(name)

def snippet_list(uid: int) -> List[str]:
    p = DATA_DIR / f"snippets_{uid}.json"
    if uid not in _snippets and p.exists():
        try:
            with open(p) as f: _snippets[uid] = json.load(f)
        except: pass
    return list(_snippets.get(uid, {}).keys())


async def interview_question(topic: str) -> str:
    prompt = (
        f"أنت محاور تقني. اطرح سؤال مقابلة حقيقي عن: {topic}\n\n"
        "### ❓ السؤال\n"
        "### 💡 تلميحات (3 فقط)\n"
        "### 🎦 المستوى [مبتدئ/متوسط/متقدم]\n"
        "### ⏰ وقت الحل المتوقع\n\n"
        "أرسل السؤال فقط — لا تعط الإجابة."
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["EXPLAINER"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=800,
    )
    return resp.choices[0].message.content


async def suggest_stack(idea: str) -> str:
    prompt = (
        f"اقترح Tech Stack مثالي لـ: {idea}\n\n"
        "### 🏆 Stack الموصى به\n"
        "### ⚖️ مقارنة 2 بدائل\n"
        "### 🚀 خطوات البدء الفوري\n"
        "### ⏰ تقدير وقت وتكلفة التطوير\n"
        "### ⚠️ تحذيرات"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["ARCHITECT"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=1600,
    )
    return resp.choices[0].message.content


async def analyze_tech_debt(code: str) -> str:
    lines   = code.split("\n")
    todos   = sum(1 for l in lines if re.search(r'#\s*(TODO|FIXME|HACK|XXX)', l, re.I))
    quality = score_code_quality(code)
    prompt = (
        f"حلّل Technical Debt:\n\n```\n{code[:3000]}\n```\n\n"
        "### 💰 تقدير الدين التقني\n"
        "### 💥 أكبر 5 مصادر\n"
        "### 📅 خطة السداد\n"
        "### ⏰ وقت التحسين المقدّر"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["ANALYST"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=1600,
    )
    debt_score = max(0, 100 - quality["score"])
    return f"🚨 **Tech Debt: {debt_score}/100** | TODOs: {todos}\n\n" + resp.choices[0].message.content


async def generate_cicd(tech: str) -> str:
    prompt = (
        f"ولد GitHub Actions CI/CD pipeline كامل لـ {tech}:\n\n"
        "1. **.github/workflows/ci.yml**\n"
        "2. **.github/workflows/cd.yml**\n"
        "3. **pre-commit hooks**\n"
        "4. **شرح كل خطوة**\n"
        "5. **GitHub Secrets المطلوبة**"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["ARCHITECT"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=2000,
    )
    return resp.choices[0].message.content


async def detect_patterns(code: str) -> str:
    prompt = (
        f"اكتشف Design Patterns:\n\n```\n{code[:3000]}\n```\n\n"
        "### 🎭 Patterns المكتشفة\n"
        "### ✅ Patterns صحيحة\n"
        "### ⚠️ Anti-Patterns\n"
        "### 💡 Patterns أفضل مقترحة"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["ANALYST"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=1600,
    )
    return resp.choices[0].message.content


async def migration_guide(from_tech: str, to_tech: str, code: str = "") -> str:
    code_ctx = f"\n\nالكود:\n```\n{code[:2000]}\n```" if code else ""
    prompt = (
        f"اعمل دليل ترحيل من {from_tech} إلى {to_tech}.{code_ctx}\n\n"
        "### 📊 تقييم التعقيد\n"
        "### 🗺️ خطوات الترحيل\n"
        "### ⚠️ التغييرات الجوهرية\n"
        "### 🛠️ أدوات مساعدة\n"
        "### 📝 مثال كود محوّل"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["ARCHITECT"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=2000,
    )
    return resp.choices[0].message.content


async def generate_env(code: str) -> str:
    env_patterns = re.findall(r'os\.(?:environ|getenv)\s*[\[\(]["\']([\w]+)["\']', code)
    prompt = (
        f"ولد .env.example لهذا الكود:\n\n```\n{code[:2500]}\n```\n\n"
        "1. **ملف .env.example** مع شرح\n"
        "2. **تصنيف المتغيرات**\n"
        "3. **قيم افتراضية آمنة**\n"
        "4. **تحذيرات الأمان**"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["SECURITY"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=1400,
    )
    detected = f"🔍 **متغيرات ({len(env_patterns)}):** {', '.join(env_patterns[:10])}\n\n" if env_patterns else ""
    return detected + resp.choices[0].message.content


async def coding_quiz(topic: str) -> str:
    prompt = (
        f"ولد تحدي برمجي يومي عن: {topic}\n\n"
        "### 📝 التحدي + المدخلات/المخرجات\n"
        "### 💡 أمثلة test cases\n"
        "### 🎦 المستوى\n"
        "### ⏰ التعقيد المطلوب\n\n"
        "أرسل التحدي فقط — الحل سيجيء بعد رد المستخدم."
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["TEST"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=800,
    )
    return resp.choices[0].message.content


# ══════════════════════════════════════════════════════════════
#  v4 COMMAND HANDLERS
# ══════════════════════════════════════════════════════════════

async def cmd_translate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = " ".join(ctx.args) if ctx.args else ""
    if not args:
        await update.message.reply_text("⚠️ `/translate python → js <كود>`", parse_mode=ParseMode.MARKDOWN)
        return
    m = re.match(r'(\w+)\s*[-→>]+\s*(\w+)\s*(.*)', args, re.DOTALL | re.I)
    if not m:
        await update.message.reply_text("⚠️ صيغة: `python → js <كود>`", parse_mode=ParseMode.MARKDOWN)
        return
    from_lang, to_lang, code = m.group(1), m.group(2), m.group(3).strip()
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""
    if not code:
        await update.message.reply_text("⚠️ أضف الكود")
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text(f"📝 تحويل {from_lang} → {to_lang}...")
    result = await translate_code(code, from_lang, to_lang)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_docker(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    desc = " ".join(ctx.args) if ctx.args else ""
    if not desc:
        await update.message.reply_text("⚠️ `/docker <وصف المشروع>`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("🐳 جاري توليد Docker files...")
    result = await generate_docker(desc)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_regex(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    desc = " ".join(ctx.args) if ctx.args else ""
    if not desc:
        await update.message.reply_text("⚠️ `/regex <وصف ما تريد>`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("🔍 بناء Regex...")
    result = await build_regex(desc)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_review(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    code = " ".join(ctx.args) if ctx.args else ""
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""
    if not code:
        code = get_user(uid)["structured_memory"]["project_context"].get("last_file", {}).get("content", "")
    if not code:
        await update.message.reply_text("⚠️ ارسل كوداً", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("🔍 Code Review...")
    result = await code_review(code)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_diff(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = " ".join(ctx.args) if ctx.args else ""
    if "|" in text:
        parts = text.split("|", 1)
        result = await diff_code(parts[0].strip(), parts[1].strip())
        if len(result) > 4000: result = result[:3990] + "\n_..._"
        await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("⚠️ `/diff <كود1> | <كود2>`", parse_mode=ParseMode.MARKDOWN)


async def cmd_snippet(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    args = ctx.args
    if not args:
        await update.message.reply_text(
            "📌 `/snippet save <اسم> <كود>`\n"
            "`/snippet get <اسم>`\n`/snippet list`\n`/snippet del <اسم>`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    sub = args[0].lower()
    if sub == "save" and len(args) >= 2:
        name = args[1]
        code = " ".join(args[2:])
        if not code and update.message.reply_to_message:
            code = update.message.reply_to_message.text or ""
        if not code:
            await update.message.reply_text("⚠️ أضف الكود")
            return
        ok = snippet_save(uid, name, code)
        await update.message.reply_text(f"✅ حفظ `{name}`", parse_mode=ParseMode.MARKDOWN)
    elif sub == "get" and len(args) >= 2:
        code = snippet_get(uid, args[1])
        if code:
            await update.message.reply_text(f"📌 `{args[1]}`:\n```\n{code[:3900]}\n```", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"❌ `{args[1]}` غير موجود", parse_mode=ParseMode.MARKDOWN)
    elif sub == "list":
        names = snippet_list(uid)
        text = "📌 **Snippets:**\n" + "\n".join(f"  • `{n}`" for n in names) if names else "💭 لا يوجد"
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    elif sub == "del" and len(args) >= 2:
        if uid in _snippets and args[1] in _snippets[uid]:
            del _snippets[uid][args[1]]
            snippet_save(uid, "_", "")
            _snippets[uid].pop("_", None)
            await update.message.reply_text(f"✅ حذف `{args[1]}`", parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(f"❌ `{args[1]}` غير موجود", parse_mode=ParseMode.MARKDOWN)


async def cmd_interview(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(ctx.args) if ctx.args else "python"
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text(f"🎬 سؤال {topic}...")
    result = await interview_question(topic)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_stack(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    idea = " ".join(ctx.args) if ctx.args else ""
    if not idea:
        await update.message.reply_text("⚠️ `/stack <فكرة>`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("🏆 تحديد Tech Stack...")
    result = await suggest_stack(idea)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_debt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    code = " ".join(ctx.args) if ctx.args else ""
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""
    if not code:
        code = get_user(uid)["structured_memory"]["project_context"].get("last_file", {}).get("content", "")
    if not code:
        await update.message.reply_text("⚠️ ارسل كوداً", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("💰 Tech Debt...")
    result = await analyze_tech_debt(code)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_cicd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    tech = " ".join(ctx.args) if ctx.args else ""
    if not tech:
        await update.message.reply_text("⚠️ `/cicd <تقنية>` مثال: `/cicd fastapi`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("⚙️ CI/CD pipeline...")
    result = await generate_cicd(tech)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_pattern(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    code = " ".join(ctx.args) if ctx.args else ""
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""
    if not code:
        code = get_user(uid)["structured_memory"]["project_context"].get("last_file", {}).get("content", "")
    if not code:
        await update.message.reply_text("⚠️ ارسل كوداً", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("🎭 Design Patterns...")
    result = await detect_patterns(code)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_migrate(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = " ".join(ctx.args) if ctx.args else ""
    if not text:
        await update.message.reply_text("⚠️ `/migrate django → fastapi`", parse_mode=ParseMode.MARKDOWN)
        return
    m = re.match(r'(\S+)\s*[-→>]+\s*(\S+)\s*(.*)', text, re.DOTALL | re.I)
    if not m:
        await update.message.reply_text("⚠️ صيغة: `from → to`", parse_mode=ParseMode.MARKDOWN)
        return
    from_t, to_t, code = m.group(1), m.group(2), m.group(3).strip()
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text(f"🗺️ ترحيل {from_t} → {to_t}...")
    result = await migration_guide(from_t, to_t, code)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_env_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    code = " ".join(ctx.args) if ctx.args else ""
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""
    if not code:
        code = get_user(uid)["structured_memory"]["project_context"].get("last_file", {}).get("content", "")
    if not code:
        await update.message.reply_text("⚠️ ارسل كوداً", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("📝 توليد .env...")
    result = await generate_env(code)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_quiz(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(ctx.args) if ctx.args else "python"
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text(f"🏆 تحدي {topic}...")
    result = await coding_quiz(topic)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


# ══════════════════════════════════════════════════════════════
#  v5 NEW MODULES (15 features)
# ══════════════════════════════════════════════════════════════

async def explain_error(error_msg: str) -> str:
    """v5 — Explain any error in simple Arabic."""
    prompt = (
        f"اشرح هذا الخطأ لمبتدئ بالعربية البسيطة:\n"
        f"```\n{error_msg[:800]}\n```\n\n"
        "### 📍 نوع الخطأ\n"
        "### 🤔 ليه حصل (بكلام بسيط)\n"
        "### 🔧 كيف تحله (خطوات واضحة)\n"
        "### 💡 كيف تتجنبه مستقبلاً"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["EXPLAINER"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=1200,
    )
    return resp.choices[0].message.content


async def generate_flowchart(code: str) -> str:
    """v5 — Generate text flowchart from code."""
    prompt = (
        f"ولد flowchart نصي لهذا الكود:\n"
        f"```\n{code[:2500]}\n```\n\n"
        "استخدم ASCII art و اسهم واضحة:\n"
        "• [Start] → للبداية\n"
        "• [خطوة] → للعمليات\n"
        "• <شرط?> → للتفرعات\n"
        "• [End] → للنهاية\n\n"
        "بعد المخطط اكتب شرحاً موجزاً."
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["EXPLAINER"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=1500,
    )
    return resp.choices[0].message.content


async def generate_standup(work_desc: str) -> str:
    """v5 — Generate daily standup report."""
    prompt = (
        f"اكتب تقرير stand-up يومي احترافي من:\n{work_desc}\n\n"
        "التنسيق:\n"
        "**✅ ما عملته أمس:**\n"
        "**🚧 ما سأعمله اليوم:**\n"
        "**🚫 عوائق:**\n"
        "**📅 التقدير الزمني:**"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a professional tech lead writing concise standup reports."},
                  {"role": "user",   "content": prompt}],
        max_tokens=600,
    )
    return resp.choices[0].message.content


async def generate_commit_msg(code_diff: str) -> str:
    """v5 — Generate conventional commit message."""
    prompt = (
        f"ولد commit message بمعيار Conventional Commits لـ:\n"
        f"```\n{code_diff[:2000]}\n```\n\n"
        "قدّم:\n"
        "1. **commit رئيسي** (feat/fix/refactor/docs/test/chore)\n"
        "2. **وصف مفصّل** (body)\n"
        "3. **3 خيارات بديلة** للمستخدم\n"
        "4. **Breaking changes** إذا وجدت"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["CODER"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=600,
    )
    return resp.choices[0].message.content


async def generate_pr_desc(code: str, title: str = "") -> str:
    """v5 — Generate Pull Request description."""
    title_ctx = f"عنوان الـ PR: {title}\n" if title else ""
    prompt = (
        f"اكتب Pull Request description احترافية:\n{title_ctx}"
        f"```\n{code[:2500]}\n```\n\n"
        "### 📋 وصف التغيير\n"
        "### 🧠 السبب\n"
        "### 🧪 كيفية الاختبار\n"
        "### ✅ Checklist\n"
        "### 📸 Screenshots (إذا انطبق)"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["CODER"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=1000,
    )
    return resp.choices[0].message.content


SCAFFOLD_TYPES = {
    "fastapi":  "FastAPI + SQLAlchemy + Alembic + Pydantic + pytest",
    "flask":    "Flask + SQLAlchemy + Flask-Migrate + pytest",
    "django":   "Django + DRF + celery + pytest-django",
    "react":    "React + TypeScript + Vite + TailwindCSS + React Router",
    "vue":      "Vue 3 + TypeScript + Pinia + Vite + Tailwind",
    "flutter":  "Flutter + Provider/Riverpod + dio + go_router",
    "node":     "Node.js + Express + TypeScript + Prisma + Jest",
    "nextjs":   "Next.js 14 + TypeScript + Tailwind + Prisma + Auth.js",
    "python":   "Python package + setuptools + pytest + black + mypy",
    "cli":      "Python CLI + Click + Rich + typer + pytest",
}

async def generate_scaffold(project_type: str) -> str:
    """v5 — Generate full project scaffold."""
    stack = SCAFFOLD_TYPES.get(project_type.lower(), project_type)
    prompt = (
        f"ولد هيكل مجلدات كامل لمشروع {project_type}:\n"
        f"Stack: {stack}\n\n"
        "1. **هيكل المجلدات** (tree واضح)\n"
        "2. **محتوى أهم الملفات** (main.py, config, models, routes)\n"
        "3. **requirements.txt / package.json**\n"
        "4. **.gitignore** مناسب\n"
        "5. **أوامر التشغيل السريع**"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["ARCHITECT"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=2000,
    )
    return resp.choices[0].message.content


async def generate_changelog(changes: str) -> str:
    """v5 — Generate CHANGELOG.md."""
    prompt = (
        f"ولد CHANGELOG.md بمعيار Keep a Changelog:\n"
        f"التغييرات:\n{changes}\n\n"
        "استخدم أقسام: Added / Changed / Fixed / Removed / Security\n"
        "أضف تاريخ و version وهمي."
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["DOCUMENTER"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=1000,
    )
    return resp.choices[0].message.content


LICENSE_TYPES = {
    "mit":      "MIT License — مفتوح كاملاً",
    "apache":   "Apache 2.0 — تجاري مع حماية براءة اختراع",
    "gpl":      "GPL v3 — Copyleft",
    "bsd":      "BSD 3-Clause",
    "agpl":     "AGPL v3 — SaaS Copyleft",
    "unlicense": "Unlicense — مجال عام كامل",
}

async def generate_license(license_type: str, author: str = "Author") -> str:
    """v5 — Generate license file."""
    lic_info = LICENSE_TYPES.get(license_type.lower(), license_type)
    prompt = (
        f"ولد ملف LICENSE كامل لـ {lic_info}\n"
        f"المؤلف: {author}\nالتاريخ: {datetime.now().year}\n"
        "أعطي نص اللايسنس كاملاً و شرح موجز لما تعنيه."
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["DOCUMENTER"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=800,
    )
    available = "📜 **الأنواع المتاحة:** " + " | ".join(LICENSE_TYPES.keys()) + "\n\n"
    return available + resp.choices[0].message.content


async def generate_roadmap(topic: str) -> str:
    """v5 — Learning roadmap generator."""
    prompt = (
        f"اعطيني خارطة طريق تعلّم كاملة وواقعية لـ: {topic}\n\n"
        "### 🎦 المستوى الابتدائي (0-3 أشهر)\n"
        "### 📈 المستوى المتوسط (3-6 أشهر)\n"
        "### 🚀 المستوى المتقدم (6-12 شهر)\n"
        "### 📚 أفضل المصادر (مجانية)\n"
        "### 💼 مشاريع تطبيقية لكل مستوى"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["EXPLAINER"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=2000,
    )
    return resp.choices[0].message.content


async def generate_cheatsheet(lang: str) -> str:
    """v5 — Cheatsheet generator."""
    prompt = (
        f"ولد cheatsheet مضغوط و عملي لـ {lang}\n\n"
        "شمل: الأوامر الأهم، الدوال الشائعة، الأنماط المتكررة، shortcuts مهمة\n"
        "استخدم code blocks و تنسيق واضح."
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["EXPLAINER"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=2000,
    )
    return resp.choices[0].message.content


async def compare_tech(tech1: str, tech2: str) -> str:
    """v5 — Compare two technologies."""
    prompt = (
        f"قارن بين {tech1} و {tech2}:\n\n"
        "| الجانب | {tech1} | {tech2} |\n"
        "اشمل في المقارنة:\n"
        "• الأداء والسرعة\n"
        "• سهولة التعلم\n"
        "• المجتمع والدعم\n"
        "• الاستخدامات المثالية\n"
        "• سوق العمل\n\n"
        f"### 🏆 متى تختار {tech1}\n"
        f"### 🥈 متى تختار {tech2}"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["EXPLAINER"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=1600,
    )
    return resp.choices[0].message.content


async def generate_nginx(description: str) -> str:
    """v5 — Nginx config generator."""
    prompt = (
        f"ولد nginx config كامل لـ: {description}\n\n"
        "1. **nginx.conf** و site config\n"
        "2. **SSL/HTTPS** مع Let's Encrypt\n"
        "3. **تطبيق أمن (rate limit, headers)**\n"
        "4. **Reverse proxy** إذا مناسب\n"
        "5. **Gzip + caching**"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["ARCHITECT"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=1800,
    )
    return resp.choices[0].message.content


async def generate_k8s(description: str) -> str:
    """v5 — Kubernetes manifests generator."""
    prompt = (
        f"ولد Kubernetes manifests كاملة لـ: {description}\n\n"
        "1. **Deployment.yaml**\n"
        "2. **Service.yaml**\n"
        "3. **Ingress.yaml**\n"
        "4. **ConfigMap.yaml + Secret.yaml**\n"
        "5. **HorizontalPodAutoscaler.yaml**\n"
        "6. **أوامر kubectl**"
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": AGENT_ROLES["ARCHITECT"]},
                  {"role": "user",   "content": prompt}],
        max_tokens=2000,
    )
    return resp.choices[0].message.content


async def show_history_summary(user: dict) -> str:
    """v5 — Conversation history summary."""
    h = user.get("history", [])
    if not h:
        return "💭 لا يوجد تاريخ محادثات بعد."
    convo = "\n".join(
        f"{'U' if m['role']=='user' else 'A'}: {m['content'][:80]}"
        for m in h[-20:]
    )
    prompt = (
        f"لخّص هذه المحادثة بالعربية في 5 نقاط فقط:\n\n{convo}\n\n"
        "اذكر: المواضيع الرئيسية، القرارات، الكود المهم."
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500,
    )
    exchanges = len(h) // 2
    return f"📜 *ملخص المحادثة* ({exchanges} تبادل)\n\n" + resp.choices[0].message.content


# v5: Reminders storage
_reminders: Dict[int, List[dict]] = {}

async def set_reminder(uid: int, text: str, minutes: int, app) -> str:
    """v5 — Set a reminder."""
    if minutes <= 0 or minutes > 1440:
        return "⚠️ الوقت يجب أن يكون بين 1 دقيقة و 1440 دقيقة (24 ساعة)."
    reminder = {"text": text, "uid": uid, "at": time.time() + minutes * 60}
    if uid not in _reminders: _reminders[uid] = []
    _reminders[uid].append(reminder)

    async def _fire():
        await asyncio.sleep(minutes * 60)
        try:
            await app.bot.send_message(
                chat_id=uid,
                text=f"⏰ *تذكير:* {text}",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            add_log(f"REMINDER_FAIL uid={uid}: {e}", "WARN")
        if uid in _reminders:
            _reminders[uid] = [r for r in _reminders[uid] if r["text"] != text]

    asyncio.create_task(_fire())
    return f"✅ تذكير مضبوط بعد *{minutes}* دقيقة:\n_{text}_"


# ══════════════════════════════════════════════════════════════
#  v5 COMMAND HANDLERS
# ══════════════════════════════════════════════════════════════

async def cmd_explain_error(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    error = " ".join(ctx.args) if ctx.args else ""
    if not error and update.message.reply_to_message:
        error = update.message.reply_to_message.text or ""
    if not error:
        await update.message.reply_text("⚠️ `/explain <رسالة الخطأ>`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("📍 تحليل الخطأ...")
    result = await explain_error(error)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_flowchart(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    code = " ".join(ctx.args) if ctx.args else ""
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""
    if not code:
        code = get_user(uid)["structured_memory"]["project_context"].get("last_file", {}).get("content", "")
    if not code:
        await update.message.reply_text("⚠️ ارسل كوداً", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("🗲️ جاري توليد المخطط...")
    result = await generate_flowchart(code)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_standup(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    desc = " ".join(ctx.args) if ctx.args else ""
    if not desc:
        await update.message.reply_text("⚠️ `/standup <وصف عملك اليوم>`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("📝 كتابة التقرير...")
    result = await generate_standup(desc)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_commit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    code = " ".join(ctx.args) if ctx.args else ""
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""
    if not code:
        code = get_user(uid)["structured_memory"]["project_context"].get("last_file", {}).get("content", "")
    if not code:
        await update.message.reply_text("⚠️ `/commit <كود أو diff>`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("📦 Commit message...")
    result = await generate_commit_msg(code)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_pr(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    args = ctx.args
    title = args[0] if args else ""
    code  = " ".join(args[1:]) if len(args) > 1 else ""
    if not code and update.message.reply_to_message:
        code = update.message.reply_to_message.text or ""
    if not code:
        code = get_user(uid)["structured_memory"]["project_context"].get("last_file", {}).get("content", "")
    if not code:
        await update.message.reply_text("⚠️ ارسل كوداً", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("📑 PR description...")
    result = await generate_pr_desc(code, title)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_scaffold(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ptype = " ".join(ctx.args).lower() if ctx.args else ""
    if not ptype:
        types_list = " | ".join(SCAFFOLD_TYPES.keys())
        await update.message.reply_text(
            f"⚠️ `/scaffold <نوع>`\nالأنواع: `{types_list}`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text(f"📁 إنشاء هيكل {ptype}...")
    result = await generate_scaffold(ptype)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_changelog(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    changes = " ".join(ctx.args) if ctx.args else ""
    if not changes and update.message.reply_to_message:
        changes = update.message.reply_to_message.text or ""
    if not changes:
        await update.message.reply_text("⚠️ `/changelog <وصف التغييرات>`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("📝 CHANGELOG...")
    result = await generate_changelog(changes)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_license(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args   = ctx.args
    ltype  = args[0].lower() if args else ""
    author = " ".join(args[1:]) if len(args) > 1 else "Author"
    if not ltype:
        await update.message.reply_text(
            f"⚠️ `/license <نوع> [<اسمك>]`\nالأنواع: `{'|'.join(LICENSE_TYPES.keys())}`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("📜 LICENSE...")
    result = await generate_license(ltype, author)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_roadmap(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(ctx.args) if ctx.args else ""
    if not topic:
        await update.message.reply_text("⚠️ `/roadmap <التقنية>` مثال: `/roadmap backend`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text(f"📍 خارطة طريق {topic}...")
    result = await generate_roadmap(topic)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_cheatsheet(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lang = " ".join(ctx.args) if ctx.args else ""
    if not lang:
        await update.message.reply_text("⚠️ `/cheatsheet <لغة/أداة>` مثال: `/cheatsheet python`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text(f"📝 Cheatsheet {lang}...")
    result = await generate_cheatsheet(lang)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_compare_tech(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = " ".join(ctx.args) if ctx.args else ""
    m    = re.match(r'(\S+)\s+(?:vs|VS|أو|or)\s+(\S+)', args, re.I)
    if not m:
        await update.message.reply_text("⚠️ `/compare <تقنية> vs <تقنية>` مثال: `/compare react vs vue`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text(f"⚖️ مقارنة {m.group(1)} vs {m.group(2)}...")
    result = await compare_tech(m.group(1), m.group(2))
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_nginx(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    desc = " ".join(ctx.args) if ctx.args else ""
    if not desc:
        await update.message.reply_text("⚠️ `/nginx <وصف>`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("🌐 Nginx config...")
    result = await generate_nginx(desc)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_k8s(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    desc = " ".join(ctx.args) if ctx.args else ""
    if not desc:
        await update.message.reply_text("⚠️ `/k8s <وصف التطبيق>`", parse_mode=ParseMode.MARKDOWN)
        return
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("⎈️ Kubernetes manifests...")
    result = await generate_k8s(desc)
    if len(result) > 4000: result = result[:3990] + "\n_..._"
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_history(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    user = get_user(uid)
    await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    msg = await update.message.reply_text("📜 ملخص المحادثة...")
    result = await show_history_summary(user)
    await msg.edit_text(result, parse_mode=ParseMode.MARKDOWN)


async def cmd_remind(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    args = ctx.args
    if not args:
        active = _reminders.get(uid, [])
        if active:
            text = "⏰ *تذكيرات نشطة:*\n"
            for r in active:
                mins_left = max(0, int((r['at'] - time.time()) / 60))
                text += f"  • {r['text'][:50]} (بعد {mins_left}د)\n"
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(
                "⚠️ `/remind <الوقت بالدقائق> <النص>`\n"
                "مثال: `/remind 30 راجع الكود`",
                parse_mode=ParseMode.MARKDOWN
            )
        return
    try:
        minutes = int(args[0])
        text    = " ".join(args[1:])
    except ValueError:
        await update.message.reply_text("⚠️ الوقت يجب أن يكون رقماً (minutes)", parse_mode=ParseMode.MARKDOWN)
        return
    if not text:
        await update.message.reply_text("⚠️ أضف نص التذكير")
        return
    result = await set_reminder(uid, text, minutes, ctx.application)
    await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN)


if __name__ == "__main__":
    main()
