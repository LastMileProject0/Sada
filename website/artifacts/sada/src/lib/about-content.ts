// Every statement below is sourced from backend docs/source (read-only):
// schemas.py (SCENARIO_ID, EventStage, ChannelID, PolicyCheckStatus), docs/agent_contracts.md,
// docs/channel_actionability.md, docs/agent3_runtime_handoff.md, docs/integration_handoff.md,
// lastmile_ai/ai/policy_explainer.py, backend/README.md. Aggregate facts only; no resident records.

export const ABOUT_CHANNELS = [
  { id: 'CH01', en: ['SMS', 'Arabic text message. Not UAE-Alert Cell Broadcast. Missing or uncertain multipart receipt stays under review.'],
    ar: ['الرسائل النصية', 'رسالة نصية عربية. ليست البث الخلوي لنظام UAE-Alert. أي استلام ناقص أو غير مؤكد للأجزاء يبقى قيد المراجعة.'] },
  { id: 'CH02', en: ['Mobile App', 'Full alert screen. Requires the app-installed flag (600 synthetic residents); installation never proves delivery or accessibility.'],
    ar: ['تطبيق الجوال', 'شاشة تحذير كاملة. تتطلب علامة تثبيت التطبيق (600 مقيم افتراضي)؛ التثبيت لا يثبت الوصول ولا الإتاحة.'] },
  { id: 'CH03', en: ['Automated Voice Call', 'Fixed Arabic text-to-speech script. Call arrival does not prove the instructions were heard or understood.'],
    ar: ['المكالمة الصوتية الآلية', 'نص صوتي عربي ثابت. وصول المكالمة لا يثبت سماع التعليمات أو فهمها.'] },
  { id: 'CH04', en: ['Public Sirens', 'Alert-only, nonverbal signal. May count toward Estimated Reach but never alone toward Effective Warning Coverage.'],
    ar: ['صفارات الإنذار العامة', 'إشارة تنبيه فقط بلا كلام. قد تُحتسب في الوصول التقديري، لكنها لا تكفي وحدها للتغطية الفعالة.'] },
  { id: 'CH05', en: ['Digital Signage', 'Fixed Arabic display text. Requires the signage-area flag; readability is checked per resident flag.'],
    ar: ['اللوحات الرقمية', 'نص عربي ثابت للعرض. يتطلب علامة منطقة اللوحات؛ وتُفحص قابلية القراءة وفق علامة كل مقيم.'] },
] as const;

export const ABOUT_STAGES = ['T+00', 'T+02', 'T+04', 'T+06'] as const;
export const ABOUT_ZONES = ['A', 'B', 'C'] as const;
export const ABOUT_SCENARIO_ID = 'AL_WADI_FLASH_FLOOD';

export const aboutT = {
  en: {
    pageTitle: 'About & Limits — SADA',
    pageDesc: 'What SADA evaluates: a fixed synthetic Al Wadi flash-flood scenario, 1,000 synthetic residents, five warning channels and four deterministic agents — and what it does not do.',
    eyebrow: 'About & Limits',
    title: 'A planning bench, not a warning system.',
    lede: 'SADA compares pre-emergency warning plans against one fixed, synthetic scenario. It shows judges how a plan might reach people, where it fails, and which alternative is recommended. Nothing here is live.',
    scenarioH: 'The fixed scenario',
    scenario: [
      ['1,000', 'synthetic residents, exactly. The approved roster is fixed and unique; no real person is represented.'],
      ['A · B · C', 'zones of the fictional Al Wadi area.'],
      ['4', 'fixed snapshots: T+00, T+02, T+04, T+06. Only the stage and enabled channels are planner-editable.'],
    ],
    scenarioNote: 'The Arabic warning text is fixed and pre-approved for every snapshot and plan. It is marked exercise only and is never rewritten by AI.',
    channelsH: 'Five approved channels',
    agentsH: 'Four deterministic agents',
    agents: [
      ['Delivery', 'Simulates whether each selected channel attempt is delivered, delayed, failed or unavailable.'],
      ['Technical risk', 'Analyses technical risks behind failed and delayed delivery.'],
      ['Accessibility & policy assessment', 'Assesses usability and policy checks against recorded attributes. An assessment, not a certification.'],
      ['Recovery', 'Proposes alternative plans P1–P3, reruns them under identical assumptions and selects one, or keeps P0 if none is suitable.'],
    ],
    agentsNote: 'Same inputs always give the same outputs. Unknown evidence stays as Needs Further Review; it is never counted as success.',
    assumptionsH: 'Accessibility & connectivity assumptions',
    assumptions: [
      'Each synthetic resident carries recorded flags such as hearing or visual impairment, age 65+, limited internet, weak mobile coverage, app installed, siren area, signage area, voice usable and signage readable.',
      'Accessibility is never inferred from a disability category alone; a known Voice usable = No or Signage readable = No after arrival is an accessibility barrier.',
      'Effective Warning Coverage requires a selected channel, arrival within 30 simulated seconds, sufficient actionable content and supported usability. Delayed (over 30 and up to 60 seconds) counts toward Estimated Reach only.',
      'Delivery timings and failure rates are modeling assumptions, not measured network behavior. Individual resident records are not shown on this site.',
    ],
    aiH: 'Where AI fits — and where it stops',
    deterministic: ['Deterministic core', 'All metrics, comparisons and the recommended plan come from the four agents. AI never changes them.'],
    ai: ['Separate, limited Qwen / RAG explanation', 'An optional read-only sidecar that explains policy questions using retrieved evidence. It may return ReviewRequired, InsufficientInformation or ModelUnavailable. Reliable, accepted bilingual explanations have not been demonstrated.'],
    limitsH: 'What SADA does not do',
    limits: [
      'It sends no live warnings and issues no real alerts.',
      'It does not monitor hazards, networks or people.',
      'It does not guarantee real-world delivery or warning performance.',
      'It does not provide legal, regulatory or CAP compliance certification.',
    ],
    ctaPlan: 'Open Planning', ctaResults: 'Compare Plans',
    toc: 'On this page', notifications: 'Notifications', noNotifications: 'No notifications. SADA does not send real alerts.',
    sources: 'Sourced from the project’s approved scenario documentation and source code.',
  },
  ar: {
    pageTitle: 'حول صدى وحدوده — صدى',
    pageDesc: 'ما يقيّمه صدى: سيناريو سيول افتراضي ثابت في منطقة الوادي، و1,000 مقيم افتراضي، وخمس قنوات تحذير، وأربعة وكلاء حتميين — وما لا يقوم به.',
    eyebrow: 'حول صدى وحدوده',
    title: 'منصة لاختبار الخطط، وليست نظام تحذير.',
    lede: 'يقارن صدى خطط التحذير المسبقة للطوارئ على سيناريو افتراضي واحد ثابت. يوضح للمحكّمين كيف قد تصل الخطة إلى الناس، وأين تخفق، وأي بديل يُوصى به. لا شيء هنا مباشر.',
    scenarioH: 'السيناريو الثابت',
    scenario: [
      ['1,000', 'مقيم افتراضي بالضبط. القائمة المعتمدة ثابتة وفريدة؛ ولا تمثل أي شخص حقيقي.'],
      ['A · B · C', 'مناطق منطقة الوادي الافتراضية.'],
      ['4', 'لقطات ثابتة: T+00 وT+02 وT+04 وT+06. المرحلة والقنوات المفعّلة فقط قابلة للتعديل.'],
    ],
    scenarioNote: 'نص التحذير العربي ثابت ومعتمد مسبقاً لكل لقطة وخطة، ومُعلَّم بأنه تدريب فقط، ولا يعيد الذكاء الاصطناعي صياغته.',
    channelsH: 'خمس قنوات معتمدة',
    agentsH: 'أربعة وكلاء حتميون',
    agents: [
      ['التوصيل', 'يحاكي ما إذا كانت كل محاولة عبر قناة مختارة قد وصلت أو تأخرت أو فشلت أو كانت غير متاحة.'],
      ['المخاطر التقنية', 'يحلل المخاطر التقنية وراء الإخفاق والتأخير.'],
      ['تقييم الإتاحة والسياسات', 'يقيّم قابلية الاستخدام وفحوص السياسات وفق السمات المسجلة. هو تقييم وليس اعتماداً رسمياً.'],
      ['التعافي', 'يقترح خططاً بديلة P1–P3 ويعيد تشغيلها بالافتراضات نفسها ثم يختار إحداها، أو يُبقي P0 إن لم توجد خطة مناسبة.'],
    ],
    agentsNote: 'المدخلات نفسها تعطي دائماً المخرجات نفسها. الأدلة غير المعروفة تبقى «بحاجة إلى مراجعة إضافية» ولا تُحتسب نجاحاً.',
    assumptionsH: 'افتراضات الإتاحة والاتصال',
    assumptions: [
      'يحمل كل مقيم افتراضي علامات مسجلة مثل الإعاقة السمعية أو البصرية، والعمر 65+، والإنترنت المحدود، وضعف تغطية الجوال، وتثبيت التطبيق، ومنطقة الصفارات، ومنطقة اللوحات، وصلاحية الصوت، وقابلية قراءة اللوحات.',
      'لا تُستنتج الإتاحة من فئة الإعاقة وحدها؛ وإذا كانت صلاحية الصوت = لا أو قابلية قراءة اللوحة = لا بعد الوصول فذلك عائق إتاحة.',
      'تتطلب التغطية الفعالة قناة مختارة، ووصولاً خلال 30 ثانية محاكاة، ومحتوى كافياً قابلاً للتنفيذ، وقابلية استخدام مدعومة. أما المتأخر (أكثر من 30 وحتى 60 ثانية) فيُحتسب في الوصول التقديري فقط.',
      'أزمنة التوصيل ونسب الإخفاق افتراضات نمذجة وليست سلوك شبكة مقاساً. لا تُعرض سجلات المقيمين الفردية في هذا الموقع.',
    ],
    aiH: 'أين يقع الذكاء الاصطناعي — وأين يتوقف',
    deterministic: ['النواة الحتمية', 'جميع المقاييس والمقارنات والخطة الموصى بها تأتي من الوكلاء الأربعة. الذكاء الاصطناعي لا يغيّرها.'],
    ai: ['شرح منفصل ومحدود عبر Qwen / RAG', 'إضافة اختيارية للقراءة فقط تشرح أسئلة السياسات اعتماداً على أدلة مسترجعة. قد تعيد ReviewRequired أو InsufficientInformation أو ModelUnavailable. لم يُثبت بعد تقديم شروح ثنائية اللغة موثوقة ومعتمدة.'],
    limitsH: 'ما لا يقوم به صدى',
    limits: [
      'لا يرسل تحذيرات مباشرة ولا يصدر تنبيهات حقيقية.',
      'لا يراقب المخاطر أو الشبكات أو الأشخاص.',
      'لا يضمن الأداء الفعلي للتوصيل أو التحذير في الواقع.',
      'لا يقدم اعتماداً قانونياً أو تنظيمياً أو اعتماد امتثال لمعيار CAP.',
    ],
    ctaPlan: 'افتح التخطيط', ctaResults: 'قارن الخطط',
    toc: 'في هذه الصفحة', notifications: 'الإشعارات', noNotifications: 'لا توجد إشعارات. لا يرسل صدى تنبيهات حقيقية.',
    sources: 'مستند إلى وثائق السيناريو المعتمدة والشيفرة المصدرية للمشروع.',
  },
};
