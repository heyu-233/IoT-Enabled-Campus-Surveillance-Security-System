export default {
  app: {
    title: 'Campus Sentinel',
    subtitle: 'IoT campus security command interface',
    welcome: 'Operational view across streams, alerts, and analytics.',
    search: 'Search', refresh: 'Refresh', save: 'Save', cancel: 'Cancel', close: 'Close', edit: 'Edit', delete: 'Delete',
    processing: 'Processing...', comingSoon: 'Data will appear once backend services are active.', noData: 'No data yet',
    notes: 'Notes', confidence: 'Confidence', location: 'Location', status: 'Status', severity: 'Severity', actions: 'Actions',
    online: 'Online', offline: 'Offline', unknown: 'Unknown', all: 'All', start: 'Start', stop: 'Stop', submit: 'Submit',
    language: 'Language', theme: 'Theme', day: 'Day', night: 'Night', streamUnavailable: 'Stream unavailable'
  },
  nav: { overview: 'Overview', monitoring: 'Monitoring', alerts: 'Alerts', behaviors: 'Behaviors', analytics: 'Analytics', system: 'System', logout: 'Logout' },
  auth: {
    signIn: 'Sign in', username: 'Username', password: 'Password', remember: 'Keep this session active on this device',
    helper: 'Use your backend account to access live monitoring and management tools.',
    tagline: 'Realtime campus awareness for operators and administrators.',
    email: 'Email',
    confirmPassword: 'Confirm password',
    createAccount: 'Create account',
    noAccount: "Don't have an account?",
    haveAccount: 'Already have an account?',
    registerHelper: 'Create a new operator account and enter the control room immediately.',
    registerSubtitle: 'Registration signs you in automatically so you can validate the workflow at once.',
    registerFeatureMonitoring: 'Review live streams, camera health, and bound device IDs.',
    registerFeatureAlerts: 'Inspect alert evidence, processing status, and historical records.',
    passwordMismatch: 'The two passwords do not match.'
  },
  overview: {
    title: 'Operational overview', headline: 'A clear control room for monitoring, response, and analysis.',
    liveRibbon: 'Campus operations ribbon', latestAlerts: 'Latest alerts', liveBehaviors: 'Behavior pulse',
    quickActions: 'Quick actions', quickActionsBody: 'Jump into the most active modules without losing context.',
    systemHealth: 'System health', cameraCoverage: 'Camera coverage', analyticsFocus: 'Analytics focus'
  },
  monitoring: {
    title: 'Live monitoring', subtitle: 'Review camera health, playback streams, and update device details.',
    addCamera: 'Add camera', editCamera: 'Edit camera', cameraDirectory: 'Camera directory', streamWindow: 'Stream window',
    details: 'Device details', refreshStatus: 'Refresh status', loadStream: 'Load stream',
    emptyStream: 'Select a camera to preview its stream.', lastActive: 'Last active', ipAddress: 'IP address',
    port: 'Port', name: 'Camera name', streamUrl: 'Stream URL'
  },
  alerts: {
    title: 'Alert management', subtitle: 'Track, review, and process generated alert records.',
    activeQueue: 'Alert queue', detail: 'Alert detail', process: 'Process alert', processedBy: 'Processed by', processedAt: 'Processed at',
    searchPlaceholder: 'Search by type, status, severity...', notesPlaceholder: 'Add handling notes for the incident record.',
    statusOpen: 'Open', statusProcessed: 'Processed', statusPending: 'Pending'
  },
  behaviors: {
    title: 'Suspicious behavior feed', subtitle: 'Live and historical detections from the edge inference pipeline.',
    feed: 'Behavior feed', liveStream: 'Realtime stream', subscribe: 'SSE connected', disconnected: 'SSE disconnected',
    image: 'Image', original: 'Original', processed: 'Processed'
  },
  analytics: {
    title: 'Analytics', subtitle: 'Trend views for event categories, alert volume, and high-risk zones.',
    typeDistribution: 'Type distribution', dailyAlerts: 'Daily alerts', areaHeatmap: 'Area heatmap', typeDetails: 'Type drill-down',
    spotlight: 'Analytics spotlight', totalEvents: 'Total events', topArea: 'Top risk area', selectedType: 'Selected type',
    trendNarrative: 'A more presentable command-room canvas for trends, hotspots, and type focus.',
    selectType: 'Choose a type', empty: 'No historical data yet. Real backend records will populate this wall.'
  },
  system: {
    title: 'System configuration', subtitle: 'Tune alerts, manage devices, and issue edge-side commands.',
    alertSettings: 'Alert settings', edgeTools: 'Edge tools', deviceManagement: 'Device management', emailNotifications: 'Email notifications',
    smsNotifications: 'SMS notifications', pushNotifications: 'Push notifications', recipients: 'Recipients', severityLevels: 'Severity levels',
    deviceId: 'Device ID', configPayload: 'Config payload', buzzer: 'Trigger buzzer'
  },
  toast: { loginSuccess: 'Signed in successfully.', loginError: 'Unable to sign in with these credentials.', saveSuccess: 'Changes saved.', deleteSuccess: 'Deleted successfully.', requestError: 'Request failed. Check backend availability.' }
}

