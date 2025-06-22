import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  HelpCircle,
  Search,
  Book,
  Zap,
  Shield,
  Settings,
  ChevronRight,
  X
} from 'lucide-react';

// Help content organized by category
const HELP_CONTENT = {
  'getting-started': {
    title: 'Getting Started',
    icon: <Zap className="h-5 w-5" />,
    articles: [
      {
        id: 'first-steps',
        title: 'First Steps with FinWave',
        content: `
# First Steps with FinWave

Welcome to FinWave! This guide will help you get up and running in minutes.

## 1. Connect Your Data Sources

Start by connecting at least one data source:

- **QuickBooks**: For financial statements and accounting data
- **Salesforce/HubSpot**: For sales pipeline and CRM metrics
- **Gusto/ADP**: For headcount and payroll data

Click the "Connect Data Source" button and follow the OAuth flow.

## 2. Wait for Initial Sync

After connecting, we'll automatically:
- Import your historical data
- Calculate key metrics
- Set up variance monitoring
- Generate initial forecasts

This usually takes 2-5 minutes.

## 3. Generate Your First Report

Once data is synced, you can:
- Generate a board-ready PDF report
- View real-time dashboards
- Set up variance alerts
- Create forecast scenarios

## Need Help?

- Use the help icon (?) for tooltips
- Check our documentation
- Contact support@finwave.io
        `
      },
      {
        id: 'understanding-metrics',
        title: 'Understanding Your Metrics',
        content: `
# Understanding Your Metrics

FinWave tracks dozens of financial and operational metrics automatically.

## Key Financial Metrics

### Revenue Metrics
- **MRR**: Monthly Recurring Revenue
- **ARR**: Annual Recurring Revenue (MRR × 12)
- **Revenue Growth**: Month-over-month growth rate

### Profitability Metrics
- **Gross Margin**: (Revenue - COGS) / Revenue
- **EBITDA**: Earnings Before Interest, Tax, Depreciation & Amortization
- **Net Income**: Bottom line profit after all expenses

### Cash Metrics
- **Burn Rate**: Monthly net cash outflow
- **Runway**: Months until cash reaches zero at current burn
- **Cash Balance**: Current cash and equivalents

## SaaS Metrics

- **CAC**: Customer Acquisition Cost
- **LTV**: Customer Lifetime Value
- **LTV:CAC Ratio**: Should be >3x for healthy unit economics
- **Churn Rate**: Monthly customer/revenue churn
- **Net Retention**: Expansion revenue from existing customers

## Operational Metrics

- **Headcount**: Total employees (FTE + contractors)
- **Revenue per FTE**: Productivity metric
- **Payroll %**: Payroll as percentage of revenue
        `
      }
    ]
  },
  'features': {
    title: 'Features',
    icon: <Book className="h-5 w-5" />,
    articles: [
      {
        id: 'variance-alerts',
        title: 'Variance Alerts Explained',
        content: `
# Variance Alerts Explained

Variance alerts help you spot issues before they become critical.

## How Alerts Work

1. **Automatic Monitoring**: We check your metrics hourly
2. **Smart Thresholds**: Pre-configured rules based on best practices
3. **Severity Levels**:
   - 🔴 **Critical**: Immediate attention needed
   - 🟡 **Warning**: Monitor closely
   - 🔵 **Info**: For your awareness

## Common Alert Types

### Revenue Alerts
- Revenue >5% below budget
- Revenue >10% below prior month
- MRR declining for 2+ months

### Cost Alerts
- COGS >10% above budget
- OpEx growing faster than revenue
- Payroll >50% of revenue

### Cash Alerts
- Runway <12 months
- Burn rate >20% above forecast
- Cash declining for 3+ months

## Managing Alerts

- **Acknowledge**: Mark as seen but keep monitoring
- **Resolve**: Mark as addressed
- **Add Notes**: Document actions taken
- **Adjust Rules**: Contact us to customize thresholds
        `
      },
      {
        id: 'scenario-planning',
        title: 'Scenario Planning Guide',
        content: `
# Scenario Planning Guide

Test "what-if" scenarios to make better decisions.

## Using the Scenario Planner

1. **Adjust Drivers**: Use sliders to change key assumptions
   - New customer growth rate
   - Churn rate
   - Headcount growth
   - Gross margin targets

2. **Apply Scenarios**: Choose from presets
   - **Base Case**: Current trajectory
   - **Conservative**: Lower growth, higher costs
   - **Aggressive**: Higher growth targets
   - **Downside**: Stress test scenario

3. **View Impact**: See instant updates to
   - Revenue forecast
   - Burn rate projection
   - Runway months
   - Cash requirements

## Best Practices

- Start with small changes (±10%)
- Compare multiple scenarios side-by-side
- Focus on controllable drivers
- Update monthly with actuals

## Uploading Custom Drivers

You can also upload Excel files with detailed assumptions:
1. Download the template
2. Fill in your assumptions
3. Upload via "Import Drivers"
        `
      }
    ]
  },
  'integrations': {
    title: 'Integrations',
    icon: <Shield className="h-5 w-5" />,
    articles: [
      {
        id: 'quickbooks-setup',
        title: 'QuickBooks Integration',
        content: `
# QuickBooks Integration

Connect QuickBooks for automatic financial data sync.

## What We Sync

- **P&L Statement**: Revenue, COGS, OpEx, Net Income
- **Balance Sheet**: Assets, Liabilities, Equity
- **Customer Data**: AR aging, customer count
- **Vendor Data**: AP aging, vendor payments

## Setup Steps

1. Click "Connect QuickBooks"
2. Log in with your QuickBooks credentials
3. Authorize FinWave access
4. Select company (if multiple)
5. Wait for initial sync (2-5 minutes)

## Sync Frequency

- **Automatic**: Every hour
- **Manual**: Click "Sync Now" anytime
- **Historical**: Last 24 months on first sync

## Troubleshooting

**Connection Failed**
- Ensure you have admin access in QuickBooks
- Check if QuickBooks subscription is active
- Try disconnecting and reconnecting

**Missing Data**
- Verify account mappings in QuickBooks
- Check date ranges in reports
- Contact support for custom mappings
        `
      }
    ]
  }
};

interface HelpCenterProps {
  defaultArticle?: string;
}

export function HelpCenter({ defaultArticle }: HelpCenterProps) {
  const [selectedCategory, setSelectedCategory] = useState('getting-started');
  const [selectedArticle, setSelectedArticle] = useState(defaultArticle || 'first-steps');
  const [searchQuery, setSearchQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  
  const currentArticle = HELP_CONTENT[selectedCategory]?.articles.find(
    a => a.id === selectedArticle
  );
  
  const searchArticles = (query: string) => {
    if (!query) return [];
    
    const results: any[] = [];
    const lowerQuery = query.toLowerCase();
    
    Object.entries(HELP_CONTENT).forEach(([categoryId, category]) => {
      category.articles.forEach(article => {
        if (
          article.title.toLowerCase().includes(lowerQuery) ||
          article.content.toLowerCase().includes(lowerQuery)
        ) {
          results.push({
            ...article,
            categoryId,
            categoryTitle: category.title
          });
        }
      });
    });
    
    return results;
  };
  
  const searchResults = searchArticles(searchQuery);
  
  return (
    <>
      {/* Help Button */}
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="outline"
              size="icon"
              onClick={() => setIsOpen(true)}
              className="fixed bottom-4 right-4 h-12 w-12 rounded-full shadow-lg"
            >
              <HelpCircle className="h-5 w-5" />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Help Center</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
      
      {/* Help Dialog */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-4xl h-[80vh]">
          <DialogHeader>
            <DialogTitle>Help Center</DialogTitle>
            <DialogDescription>
              Find answers to common questions and learn how to use FinWave
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid grid-cols-12 gap-6 h-full">
            {/* Sidebar */}
            <div className="col-span-4 space-y-4">
              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search help articles..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>
              
              <ScrollArea className="h-[500px]">
                {searchQuery ? (
                  // Search Results
                  <div className="space-y-2">
                    <p className="text-sm text-muted-foreground px-3">
                      {searchResults.length} results
                    </p>
                    {searchResults.map(result => (
                      <Button
                        key={result.id}
                        variant="ghost"
                        className="w-full justify-start"
                        onClick={() => {
                          setSelectedCategory(result.categoryId);
                          setSelectedArticle(result.id);
                          setSearchQuery('');
                        }}
                      >
                        <div className="text-left">
                          <p className="font-medium">{result.title}</p>
                          <p className="text-xs text-muted-foreground">
                            {result.categoryTitle}
                          </p>
                        </div>
                      </Button>
                    ))}
                  </div>
                ) : (
                  // Category Navigation
                  <div className="space-y-6">
                    {Object.entries(HELP_CONTENT).map(([categoryId, category]) => (
                      <div key={categoryId}>
                        <div className="flex items-center gap-2 px-3 mb-2">
                          {category.icon}
                          <h3 className="font-semibold">{category.title}</h3>
                        </div>
                        <div className="space-y-1">
                          {category.articles.map(article => (
                            <Button
                              key={article.id}
                              variant={selectedArticle === article.id ? 'secondary' : 'ghost'}
                              className="w-full justify-between"
                              onClick={() => {
                                setSelectedCategory(categoryId);
                                setSelectedArticle(article.id);
                              }}
                            >
                              <span>{article.title}</span>
                              <ChevronRight className="h-4 w-4" />
                            </Button>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </div>
            
            {/* Content */}
            <div className="col-span-8">
              <ScrollArea className="h-[550px] pr-4">
                {currentArticle && (
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown>{currentArticle.content}</ReactMarkdown>
                  </div>
                )}
              </ScrollArea>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}

// Standalone Tooltip Component for inline help
interface HelpTooltipProps {
  content: string;
  children: React.ReactNode;
}

export function HelpTooltip({ content, children }: HelpTooltipProps) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="inline-flex items-center gap-1 cursor-help">
            {children}
            <HelpCircle className="h-3 w-3 text-muted-foreground" />
          </span>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs">
          <p className="text-sm">{content}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}