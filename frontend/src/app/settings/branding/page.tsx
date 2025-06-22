"use client"

import React, { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useToast } from '@/components/ui/use-toast'
import { Loader2, Upload, Palette, Building2, Eye } from 'lucide-react'

interface BrandTheme {
  company_name: string
  logo_url: string
  primary_color: string
  secondary_color: string
}

export default function BrandingSettings() {
  const [theme, setTheme] = useState<BrandTheme>({
    company_name: '',
    logo_url: '',
    primary_color: '#4F46E5',
    secondary_color: '#7C3AED'
  })
  const [logoFile, setLogoFile] = useState<File | null>(null)
  const [logoPreview, setLogoPreview] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const { toast } = useToast()

  // Load current theme settings
  useEffect(() => {
    fetchCurrentTheme()
  }, [])

  const fetchCurrentTheme = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/workspaces/current/theme', {
        headers: {
          'Authorization': 'Bearer dev-token' // For development
        }
      })
      if (response.ok) {
        const data = await response.json()
        setTheme(data)
        if (data.logo_url) {
          setLogoPreview(data.logo_url)
        }
      }
    } catch (error) {
      console.error('Failed to fetch theme:', error)
      toast({
        title: "Error",
        description: "Failed to load current theme settings",
        variant: "destructive"
      })
    } finally {
      setLoading(false)
    }
  }

  const handleLogoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml']
    if (!validTypes.includes(file.type)) {
      toast({
        title: "Invalid file type",
        description: "Please upload a PNG, JPG, or SVG file",
        variant: "destructive"
      })
      return
    }

    // Validate file size (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      toast({
        title: "File too large",
        description: "Please upload a file smaller than 2MB",
        variant: "destructive"
      })
      return
    }

    setLogoFile(file)
    
    // Create preview
    const reader = new FileReader()
    reader.onloadend = () => {
      setLogoPreview(reader.result as string)
    }
    reader.readAsDataURL(file)
  }

  const handleSave = async () => {
    setSaving(true)
    
    try {
      // First upload logo if changed
      let logoUrl = theme.logo_url
      if (logoFile) {
        const formData = new FormData()
        formData.append('logo', logoFile)
        
        const uploadResponse = await fetch('/api/workspaces/current/upload-logo', {
          method: 'POST',
          headers: {
            'Authorization': 'Bearer dev-token' // For development
          },
          body: formData
        })
        
        if (!uploadResponse.ok) {
          throw new Error('Failed to upload logo')
        }
        
        const uploadData = await uploadResponse.json()
        logoUrl = uploadData.logo_url
      }

      // Save theme settings
      const response = await fetch('/api/workspaces/current/theme', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer dev-token' // For development
        },
        body: JSON.stringify({
          ...theme,
          logo_url: logoUrl
        })
      })

      if (!response.ok) {
        throw new Error('Failed to save theme')
      }

      toast({
        title: "Success",
        description: "Brand theme saved successfully"
      })
    } catch (error) {
      console.error('Failed to save theme:', error)
      toast({
        title: "Error",
        description: "Failed to save theme settings",
        variant: "destructive"
      })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Brand Settings</h1>
        <p className="text-gray-600">Customize your company's branding and visual identity</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Settings Form */}
        <div className="space-y-6">
          {/* Company Info */}
          <Card className="p-6">
            <div className="flex items-center mb-4">
              <Building2 className="w-5 h-5 mr-2" />
              <h2 className="text-xl font-semibold">Company Information</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="company-name">Company Name</Label>
                <Input
                  id="company-name"
                  type="text"
                  value={theme.company_name}
                  onChange={(e) => setTheme({ ...theme, company_name: e.target.value })}
                  placeholder="Enter your company name"
                  className="mt-1"
                />
              </div>
            </div>
          </Card>

          {/* Logo Upload */}
          <Card className="p-6">
            <div className="flex items-center mb-4">
              <Upload className="w-5 h-5 mr-2" />
              <h2 className="text-xl font-semibold">Company Logo</h2>
            </div>
            
            <div className="space-y-4">
              {logoPreview && (
                <div className="w-full h-32 bg-gray-50 rounded-lg flex items-center justify-center p-4">
                  <img 
                    src={logoPreview} 
                    alt="Company logo preview" 
                    className="max-h-full max-w-full object-contain"
                  />
                </div>
              )}
              
              <div>
                <Label htmlFor="logo-upload" className="cursor-pointer">
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
                    <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                    <p className="text-sm text-gray-600">Click to upload logo</p>
                    <p className="text-xs text-gray-500 mt-1">PNG, JPG or SVG (max 2MB)</p>
                  </div>
                </Label>
                <Input
                  id="logo-upload"
                  type="file"
                  accept="image/png,image/jpeg,image/jpg,image/svg+xml"
                  onChange={handleLogoUpload}
                  className="hidden"
                />
              </div>
            </div>
          </Card>

          {/* Colors */}
          <Card className="p-6">
            <div className="flex items-center mb-4">
              <Palette className="w-5 h-5 mr-2" />
              <h2 className="text-xl font-semibold">Brand Colors</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <Label htmlFor="primary-color">Primary Color</Label>
                <div className="flex items-center gap-2 mt-1">
                  <Input
                    id="primary-color"
                    type="color"
                    value={theme.primary_color}
                    onChange={(e) => setTheme({ ...theme, primary_color: e.target.value })}
                    className="w-20 h-10 cursor-pointer"
                  />
                  <Input
                    type="text"
                    value={theme.primary_color}
                    onChange={(e) => setTheme({ ...theme, primary_color: e.target.value })}
                    placeholder="#4F46E5"
                    className="flex-1"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="secondary-color">Secondary Color</Label>
                <div className="flex items-center gap-2 mt-1">
                  <Input
                    id="secondary-color"
                    type="color"
                    value={theme.secondary_color}
                    onChange={(e) => setTheme({ ...theme, secondary_color: e.target.value })}
                    className="w-20 h-10 cursor-pointer"
                  />
                  <Input
                    type="text"
                    value={theme.secondary_color}
                    onChange={(e) => setTheme({ ...theme, secondary_color: e.target.value })}
                    placeholder="#7C3AED"
                    className="flex-1"
                  />
                </div>
              </div>
            </div>
          </Card>

          {/* Save Button */}
          <Button 
            onClick={handleSave} 
            disabled={saving}
            className="w-full"
            size="lg"
          >
            {saving ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Saving...
              </>
            ) : (
              'Save Changes'
            )}
          </Button>
        </div>

        {/* Live Preview */}
        <div className="lg:sticky lg:top-6">
          <Card className="p-6">
            <div className="flex items-center mb-4">
              <Eye className="w-5 h-5 mr-2" />
              <h2 className="text-xl font-semibold">Live Preview</h2>
            </div>

            <div className="border rounded-lg overflow-hidden">
              {/* Preview Header */}
              <div 
                className="p-6 text-white"
                style={{ backgroundColor: theme.primary_color }}
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-4">
                    {logoPreview ? (
                      <img 
                        src={logoPreview} 
                        alt="Logo" 
                        className="h-10 w-auto bg-white p-1 rounded"
                      />
                    ) : (
                      <div className="h-10 w-10 bg-white/20 rounded" />
                    )}
                    <h3 className="text-xl font-semibold">
                      {theme.company_name || 'Your Company'}
                    </h3>
                  </div>
                  <div className="text-sm opacity-90">
                    Financial Report
                  </div>
                </div>
              </div>

              {/* Preview Content */}
              <div className="p-6 bg-gray-50">
                <div className="mb-4">
                  <h4 className="text-lg font-semibold mb-2">Executive Summary</h4>
                  <p className="text-gray-600 text-sm">
                    This preview shows how your branding will appear on reports and documents.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div 
                    className="p-4 rounded-lg text-white"
                    style={{ backgroundColor: theme.primary_color }}
                  >
                    <div className="text-2xl font-bold">$125,000</div>
                    <div className="text-sm opacity-90">Total Revenue</div>
                  </div>
                  <div 
                    className="p-4 rounded-lg text-white"
                    style={{ backgroundColor: theme.secondary_color }}
                  >
                    <div className="text-2xl font-bold">$85,000</div>
                    <div className="text-sm opacity-90">Net Profit</div>
                  </div>
                </div>

                <div className="mt-4 flex gap-2">
                  <Button 
                    size="sm"
                    style={{ 
                      backgroundColor: theme.primary_color,
                      borderColor: theme.primary_color 
                    }}
                    className="text-white hover:opacity-90"
                  >
                    View Details
                  </Button>
                  <Button 
                    size="sm"
                    variant="outline"
                    style={{ 
                      color: theme.secondary_color,
                      borderColor: theme.secondary_color 
                    }}
                    className="hover:opacity-90"
                  >
                    Export PDF
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}