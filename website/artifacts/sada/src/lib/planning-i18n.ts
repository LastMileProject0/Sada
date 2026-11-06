import type { Stage, ChannelId } from '@/lib/planning-state';

type Dict = {
  title: string; subtitle: string; stageTitle: string; stageHint: string;
  channelsTitle: string; channelsHint: string; enabled: string; disabled: string;
  toggleLabel: (name: string) => string; lastChannel: string;
  channels: Record<ChannelId, { name: string; desc: string }>;
  infoTitle: string; snapshot: string; scenario: string; population: string; populationValue: string;
  zones: string; boundaries: string; boundariesText: string; readonly: string;
  stages: Record<Stage, string>; cumulative: string;
  summaryTitle: string; selectedStage: string; enabledChannels: (n: number) => string; run: string;
  pendingTitle: string; pendingBody: string; pendingSaved: string; pendingNoResults: string;
  stageGroup: string; channelGroup: string; statusStage: (s: string) => string; close: string; comingSoon: string;
};

export const planningT: Record<'en' | 'ar', Dict> = {
  en: {
    title: 'Planning Studio',
    subtitle: 'Planners choose a snapshot stage and enabled channels before evaluation.',
    stageTitle: 'Select Snapshot Stage', stageHint: 'Stages are cumulative event snapshots.',
    channelsTitle: 'Select Enabled Channels', channelsHint: 'Enable one or more channels for evaluation.',
    enabled: 'Enabled', disabled: 'Disabled',
    toggleLabel: (n) => `Enable ${n}`,
    lastChannel: 'At least one channel must stay enabled. Enable another channel before disabling this one.',
    channels: {
      CH01: { name: 'SMS', desc: 'Model Arabic text-message delivery; not Cell Broadcast.' },
      CH02: { name: 'Mobile App', desc: 'Model a full alert screen for profiles with the app-installed flag.' },
      CH03: { name: 'Automated Voice Call', desc: 'Model delivery of a fixed Arabic text-to-speech script.' },
      CH04: { name: 'Public Sirens', desc: 'Model an alert-only signal for profiles in a siren area.' },
      CH05: { name: 'Digital Signage', desc: 'Model fixed Arabic display text for profiles in a signage area.' },
    },
    infoTitle: 'Selected Stage Information', snapshot: 'Event Snapshot', scenario: 'Scenario Name',
    population: 'Population (Synthetic)', populationValue: 'synthetic residents', zones: 'Zones',
    boundaries: 'Model Boundaries',
    boundariesText: 'Evaluation is limited to zones A, B and C only, with simplified assumptions for population and communications.',
    readonly: 'Read-only on this page',
    stages: {
      'T+00': 'Initial scenario conditions.',
      'T+02': 'SMS outage in Zone B.',
      'T+04': 'Cumulative scenario including EV02 accessibility barriers.',
      'T+06': 'EV01 and EV02 remain active. EV03 review concerns an excluded hypothetical external route; it does not mean external sharing occurred.',
    },
    cumulative: 'Each stage includes all events of earlier stages.',
    summaryTitle: 'Mission-Control Summary', selectedStage: 'Selected Stage',
    enabledChannels: (n) => `Enabled Channels (${n})`, run: 'Run Evaluation',
    pendingTitle: 'Evaluation not started',
    pendingBody: 'Choose a snapshot and channels, then open Testing & Simulation to request an evaluation.',
    pendingSaved: 'Your selected configuration:',
    pendingNoResults: 'Results are available only after a completed evaluation.',
    stageGroup: 'Snapshot stage', channelGroup: 'Warning channels',
    statusStage: (s) => `Selected stage ${s}`, close: 'Close',
    comingSoon: 'Use the sidebar to open Planning, Testing & Simulation, Compare Plans, Readiness & Resilience, Report Center, or About & Limits.',
  },
  ar: {
    title: 'استوديو التخطيط',
    subtitle: 'يختار المخططون مرحلة اللقطة الزمنية والقنوات المفعّلة قبل إجراء التقييم.',
    stageTitle: 'اختر مرحلة اللقطة الزمنية', stageHint: 'المراحل لقطات تراكمية للأحداث.',
    channelsTitle: 'اختر القنوات المفعّلة', channelsHint: 'يمكن تفعيل قناة واحدة أو أكثر للتقييم.',
    enabled: 'مفعّل', disabled: 'معطّل',
    toggleLabel: (n) => `تفعيل ${n}`,
    lastChannel: 'يجب أن تبقى قناة واحدة على الأقل مفعّلة. فعّل قناة أخرى قبل تعطيل هذه القناة.',
    channels: {
      CH01: { name: 'الرسائل النصية', desc: 'نمذجة توصيل رسائل نصية عربية؛ وليست البث الخلوي.' },
      CH02: { name: 'تطبيق الجوال', desc: 'نمذجة شاشة تحذير كاملة للملفات التي تحمل علامة تثبيت التطبيق.' },
      CH03: { name: 'الاتصال الصوتي الآلي', desc: 'نمذجة توصيل نص صوتي عربي ثابت.' },
      CH04: { name: 'صفارات الإنذار العامة', desc: 'نمذجة إشارة تنبيه فقط للملفات الموجودة في منطقة الصفارات.' },
      CH05: { name: 'الشاشات الرقمية', desc: 'نمذجة نص عربي ثابت للملفات الموجودة في منطقة اللوحات.' },
    },
    infoTitle: 'معلومات المرحلة المحددة', snapshot: 'اللقطة الزمنية للحدث', scenario: 'اسم السيناريو',
    population: 'السكان (تركيبي)', populationValue: 'مقيم تركيبي', zones: 'المناطق المعنية',
    boundaries: 'حدود النموذج',
    boundariesText: 'يقتصر التقييم على المناطق A وB وC فقط، مع افتراضات مبسطة للسكان والاتصالات.',
    readonly: 'للعرض فقط في هذه الصفحة',
    stages: {
      'T+00': 'الظروف الأولية للسيناريو.',
      'T+02': 'انقطاع الرسائل النصية في المنطقة B.',
      'T+04': 'سيناريو تراكمي يشمل عوائق الإتاحة EV02.',
      'T+06': 'تظل شروط EV01 وEV02 مفعّلة. تتعلق مراجعة EV03 بمسار خارجي افتراضي مستبعد، ولا تعني حدوث مشاركة خارجية.',
    },
    cumulative: 'تشمل كل مرحلة جميع أحداث المراحل السابقة.',
    summaryTitle: 'ملخص غرفة العمليات', selectedStage: 'المرحلة المختارة',
    enabledChannels: (n) => `القنوات المفعّلة (${n})`, run: 'تشغيل التقييم',
    pendingTitle: 'لم يبدأ التقييم',
    pendingBody: 'اختر لقطة زمنية وقنوات، ثم افتح الاختبار والمحاكاة لطلب تقييم.',
    pendingSaved: 'الإعدادات التي اخترتها:',
    pendingNoResults: 'تتوفر النتائج بعد اكتمال التقييم فقط.',
    stageGroup: 'مرحلة اللقطة الزمنية', channelGroup: 'قنوات التحذير',
    statusStage: (s) => `المرحلة المختارة ${s}`, close: 'إغلاق',
    comingSoon: 'استخدم القائمة الجانبية لفتح التخطيط أو الاختبار والمحاكاة أو مقارنة الخطط أو الجاهزية والمرونة أو مركز التقارير أو عن صدى وحدوده.',
  },
};
