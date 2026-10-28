"""Indicator definitions, heuristic lexicon and TraceCheck content. Single source of truth for backend and UI."""
import re

ENGINE_LABELS = {
    "llm": "Engine: Live LLM Extraction",
    "fallback": "Engine: Demonstration Fallback (Deterministic)",
}
GAUGE_DISCLAIMER = "This score indicates the intensity of observable communication signals, not the probability of a PSYOP."
DISCLAIMER = (
    "This tool evaluates rhetorical and structural signals only. "
    "It does not evaluate truth value or establish coordinated deceptive intent."
)
MIN_ASSESSED = 3
MAX_CHARS = 60_000
BANDS = [(25, "Low"), (50, "Moderate"), (75, "Elevated"), (100, "High")]

INDICATORS = [
    (1, "Emotional Triggering / Moral Outrage", "Loaded language designed to provoke visceral anger, fear, or disgust."),
    (2, "False Urgency & Call-to-Spread", "Demands for immediate sharing or panic reaction before verification (\"Share before deleted!\")."),
    (3, "Absolutist / Hyperbolic Phrasing", "Unqualified universal statements (\"everyone knows\", \"never\", \"completely destroyed\")."),
    (4, "Ad Hominem / Source Smearing", "Attacking an individual or entity's identity or character rather than addressing evidence."),
    (5, "False Dilemma (Binary Framing)", "Forcing multi-variable issues into a binary \"us vs. them\" choice."),
    (6, "Vague or Unverifiable Sourcing", "Attributing claims to anonymous \"insiders\", \"whistleblowers\", or unspecified \"studies\"."),
    (7, "Cherry-Picked Context / Quote Mining", "Truncated quotes or isolated statistics stripped of necessary baseline context."),
    (8, "Whataboutism / Tu Quoque", "Deflecting from the topic by introducing unrelated accusations against an opponent."),
    (9, "Loaded Framing / Question Begging", "Leading questions assuming unproven premises as established facts."),
    (10, "Conspiracy Ideation / Omnipotent Malice", "Implying a coordinated, hidden cabal behind ordinary or systemic events."),
    (11, "Fabricated Consensus / Astroturf Markers", "Suggesting unanimous public consensus via slogans, coordinated hashtags, or unsourced \"everyone agrees\" claims."),
    (12, "Algorithmic Bait / Engagement Hooks", "Explicit patterns optimized for algorithmic engagement loops."),
    (13, "Appeal to False Authority", "Citing figures outside their domain or using vague credentials to lend authority."),
    (14, "Sensationalized Headline/Text Mismatch", "Lead/headline makes claims unsupported by the body copy."),
    (15, "Euphemistic / Dysphemistic Relabeling", "Asymmetric vocabulary softening actions of an in-group while demonizing an out-group."),
    (16, "Omission of Opposing Explanations", "Absence of obvious counter-arguments, standard refutations, or official statements."),
    (17, "Temporal Displacement", "Repurposing older events or media to manufacture relevance to an active breaking crisis."),
    (18, "Linguistic Mimicry / Spoofed Credibility", "Formal, pseudo-journalistic or pseudo-academic syntax masking speculation."),
    (19, "Scapegoating / Target Simplification", "Singling out a specific group or entity as the sole cause of systemic problems."),
    (20, "Defeatism / Learned Helplessness Induction", "Demoralizing rhetoric designed to induce civic cynicism, apathy, or fatalism."),
]
NAMES = {i: n for i, n, _ in INDICATORS}

# Indicators the regex engine cannot judge: they need comparison, external metadata or semantic reading.
FALLBACK_UNASSESSABLE = {
    7: "Needs the original, untruncated source to compare against; a keyword scan cannot detect missing context.",
    14: "Needs a separate headline/lead to compare with the body copy; not determinable by pattern matching.",
    15: "Asymmetric vocabulary requires semantic comparison of how in-group and out-group actions are described.",
    16: "Absence of counter-arguments cannot be established from a keyword scan; needs knowledge of the wider topic.",
    17: "Needs external publication dates or the original media provenance, which are not in the pasted text.",
}

_F = re.IGNORECASE
HEURISTICS = {
    1: r"\b(outrag\w*|disgust\w*|horrif\w*|terrif\w*|evil|vile|sickening|shocking|devastat\w*|furious|disgrace\w*|nightmare|panic\w*|atrocit\w*)\b",
    2: r"\b(share (this )?(now|before|immediately|asap)|before (it|they|this)\b[^.!?\n]{0,30}\b(delete\w*|removed|taken down|banned|censor\w*)|spread the word|repost this|act now|go viral|everyone (needs|must) (to )?(see|know|share))",
    3: r"\b(everyone knows|nobody|no one (ever|can)|always|never|completely|totally|absolutely|100%|undeniabl\w*|without (a )?doubt|every single|proven fact|obviously)\b",
    4: r"\b(idiots?|liars?|corrupt|puppets?|shills?|clowns?|scum|morons?|stupid|crooks?|traitors?|sheep|sheeple)\b",
    5: r"(\beither (you|we|they)\b[^.!?\n]{0,60}\bor\b|\bwith us or against us\b|\bus (vs\.?|versus) them\b|\bonly two (choices|options)\b|\bthere is no (middle|other)\b)",
    6: r"\b(insiders?|whistleblowers?|anonymous (sources?|officials?)|sources (say|close to|familiar)|experts (say|agree|warn)|studies (show|prove|say)|a (recent )?study|they say|people are saying|reportedly|unnamed)\b",
    8: r"\b(what about|where was (the )?outrage|funny how)\b",
    9: r"(\bwhy (won'?t|don'?t|doesn'?t|are they|is the media) [^?\n]{0,80}\?|\bisn'?t it (obvious|strange|convenient|funny)\b|\bwho benefits\?)",
    10: r"\b(cabal|hidden hand|deep state|globalists?|puppet ?masters?|cover[- ]?up|they don'?t want you to know|behind the scenes|orchestrated|false flag)\b",
    11: r"(\b(everyone|everybody) (agrees|knows)\b|\bthe whole (world|country) (knows|agrees)\b|\bmillions (agree|know)\b|#\w+)",
    12: r"(\blike (and|&) (share|subscribe)\b|\bcomment (below|your)\b|\btag (a friend|someone)\b|\byou won'?t believe\b|\bwhat happens next\b|\blink in bio\b|\b(retweet|share) if\b|\bfollow (for|me)\b)",
    13: r"(\bas a (doctor|scientist|expert)\b|\btrust me\b|\baccording to (a |an )?(top|senior|high-ranking) (official|expert|source)\b|\b(leading|top|renowned) experts?\b)",
    18: r"\b(breaking|developing story|exclusive|unconfirmed reports?|sources indicate|according to reports|officially confirmed)\b",
    19: r"(\bblame\b|\b(the|these|those) \w+ are (the reason|to blame|responsible for|destroying|ruining)\b|\bthe (sole|only|real) (cause|reason|problem)\b|\broot of all\b)",
    20: r"\b(nothing (will|ever) (change|work)|(it'?s|it is) (all )?(pointless|hopeless|rigged)|no point (in|voting)|why bother|they'?re all the same|give up|nothing matters|your vote (doesn'?t|won'?t))\b",
}
HEURISTIC_PATTERNS = {i: re.compile(p, _F) for i, p in HEURISTICS.items()}

SAMPLE_TEXT = (
    "BREAKING: Massive explosion reported near a major government building. Insiders say officials are hiding "
    "the truth and everyone knows the media will never report it. Why won't they tell us who is really behind this? "
    "Share before they delete this! Nothing will ever change, the whole system is rigged. #WakeUp"
)

TRACE_CLAIM = (
    "BREAKING: Large explosion reported near a major government building, smoke visible. Anonymous sources say "
    "officials are covering it up. Share this now before it gets deleted!"
)

TRACE_STAGES = [
    {"title": "Source", "summary": "Who is behind the account that posted this?", "questions": [
        "Is this a verified or long-established account, or one that only looks official (lookalike name, paid badge)?",
        "Do I know who runs it and what they have reported accurately before?",
        "Does the account link to a real organisation I can check independently?"]},
    {"title": "Creation", "summary": "How was the image, video or claim made?", "questions": [
        "Could the image be AI-generated or edited (warped text, odd geometry, impossible details)?",
        "Is there an original file, metadata or a reverse-image-search match to an earlier use?",
        "Does anything in the frame (signs, weather, landmarks) contradict the claimed place or time?"]},
    {"title": "Publication", "summary": "Where did it first appear?", "questions": [
        "Has any outlet with editorial accountability published it, or only reposts of the same post?",
        "Where and when did it first appear, and is that the same story being told now?",
        "Have official channels (agency, emergency services) said anything yet?"]},
    {"title": "Amplification", "summary": "Who is pushing it and how fast?", "questions": [
        "Are many new or low-history accounts posting near-identical wording?",
        "Does the engagement look out of proportion to the account's usual reach?",
        "Is the post built to be shared (urgency, outrage, 'before it's deleted')?"]},
    {"title": "Sharing", "summary": "What happens if I pass it on?", "questions": [
        "What am I adding by sharing, and would I be comfortable if it turned out wrong?",
        "Can I wait ten minutes for confirmation before reposting?",
        "Could I share a verified source instead of this post?"]},
    {"title": "Audience", "summary": "Who will see it and what might they do?", "questions": [
        "Who in my network is likely to act on this (panic, markets, safety decisions)?",
        "Would a correction reach everyone who saw the original?",
        "Is there a trusted person I can ask before this reaches others?"]},
]
