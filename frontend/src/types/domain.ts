export type ThemeMode = 'day' | 'night'
export type LocaleMode = 'en' | 'zh'

export interface UserDto { id: number; username: string; email: string; role: string; createdAt?: string }
export interface AuthResponse { token: string; user: UserDto }
export interface LoginRequest { username: string; password: string }
export interface RegisterRequest { username: string; password: string; email: string }
export interface Camera { id?: number; name: string; deviceId?: string; ipAddress?: string; port?: number; location?: string; status?: string; streamUrl?: string; lastActive?: string; createdAt?: string; updatedAt?: string }
export interface Behavior { id?: number; cameraId?: number; type: string; description?: string; imageUrl?: string; originalImageUrl?: string; processedImageUrl?: string; confidence?: number; occurredAt?: string; createdAt?: string }
export interface Alert { id?: number; behaviorId?: number; type: string; severity?: string; status?: string; description?: string; processedBy?: string; processingNotes?: string; processedAt?: string; createdAt?: string; screenshot?: string; originalImageUrl?: string; processedImageUrl?: string; confidence?: number; behaviorOccurredAt?: string; cameraId?: number; cameraName?: string; cameraLocation?: string }
export interface AlertSetting { id?: number; emailNotifications?: boolean; smsNotifications?: boolean; pushNotifications?: boolean; emailRecipients?: string; smsRecipients?: string; severityLevels?: string; updatedAt?: string }
export interface MetricItem { label: string; value: string | number; tone?: 'normal' | 'good' | 'warning' | 'danger' }
export interface ToastMessage { id: number; tone: 'info' | 'success' | 'warning' | 'danger'; text: string }
export interface AlertPopup { id: number; alertId?: number; title: string; body: string; severity?: string; location?: string; imageUrl?: string }
export interface OptionPoint { name: string; value: number }
export interface PagedResponse<T> { items: T[]; total: number; page: number; pageSize: number }
export interface AlertProcessRequest { processedBy: string; processingNotes: string; status: 'UNPROCESSED' | 'PROCESSING' | 'PROCESSED' }
export interface EdgeCommandResponse { success: boolean; message: string; timestamp: string }
