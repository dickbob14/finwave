import { redirect } from 'next/navigation'

export default function SettingsPage() {
  // Redirect to the branding page by default
  redirect('/settings/branding')
}