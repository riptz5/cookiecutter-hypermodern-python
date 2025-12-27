'use client'

import { useCostData, useCostProjection } from '@/hooks'
import { Card, CardContent, CardHeader, CardTitle, Badge } from '@/components/ui'
import { AlertCircle, TrendingUp } from 'lucide-react'

interface CostBreakdown {
  [key: string]: number
}

export default function CostTracker() {
  const { data: costData, isLoading: costLoading } = useCostData()
  const { data: projection, isLoading: projectionLoading } = useCostProjection()

  const actualSpent = costData?.actualSpent || 0
  const costPerCycle = costData?.costPerCycle || 1.60
  const breakdown = costData?.breakdown || {}
  const projectedMonthly = projection?.projectedMonthly || 192
  const dailyAverage = actualSpent ? (actualSpent / Math.max(1, costData?.currentCycleCount || 1)) * 4 : 0

  const isOverBudget = dailyAverage > 5.0
  const isWarning = dailyAverage > 3.0

  return (
    <Card className="col-span-1">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>💰 Cost Tracker</span>
          <Badge
            variant={
              isOverBudget
                ? 'destructive'
                : isWarning
                ? 'warning'
                : 'default'
            }
          >
            {isOverBudget ? 'Over Budget' : isWarning ? 'Warning' : 'Normal'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current Spend */}
        <div>
          <p className="text-sm text-slate-400">Total Spent</p>
          <p className="text-3xl font-bold text-white">
            ${actualSpent.toFixed(2)}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            {costData?.currentCycleCount || 0} cycles × $
            {costPerCycle.toFixed(2)}
          </p>
        </div>

        {/* Daily Average with Alert */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm text-slate-400">Daily Average</p>
            {isOverBudget && (
              <AlertCircle className="w-4 h-4 text-red-500" />
            )}
          </div>
          <div className="flex items-baseline gap-2">
            <p className="text-2xl font-semibold text-white">
              ${dailyAverage.toFixed(2)}
            </p>
            <p className={`text-sm ${
              isOverBudget
                ? 'text-red-400'
                : isWarning
                ? 'text-yellow-400'
                : 'text-green-400'
            }`}>
              {isOverBudget
                ? 'Over $5/day limit'
                : isWarning
                ? 'Approaching $5/day limit'
                : 'Within budget'}
            </p>
          </div>
        </div>

        {/* Monthly Projection */}
        <div className="bg-slate-700/50 rounded p-4">
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp className="w-4 h-4 text-blue-400" />
            <p className="text-sm font-medium text-slate-300">
              Monthly Projection
            </p>
          </div>
          <p className="text-2xl font-bold text-blue-400">
            ${projectedMonthly.toFixed(2)}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Based on {costData?.currentCycleCount || 1} completed cycle(s)
          </p>
        </div>

        {/* Cost Breakdown */}
        <div>
          <p className="text-sm font-medium text-slate-300 mb-3">
            Cost Breakdown (per cycle)
          </p>
          <div className="space-y-2">
            {Object.entries(breakdown).map(([service, cost]) => (
              <div key={service} className="flex justify-between text-sm">
                <span className="text-slate-400 capitalize">
                  {service.replace(/([A-Z])/g, ' $1').trim()}
                </span>
                <span className="text-slate-300 font-medium">
                  ${(cost as number).toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Annual Projection */}
        <div className="bg-slate-700/30 border border-slate-700 rounded p-3">
          <p className="text-xs text-slate-400 mb-1">Annual Estimate</p>
          <p className="text-xl font-bold text-white">
            ${(projectedMonthly * 12).toFixed(2)}
          </p>
        </div>

        {isOverBudget && (
          <div className="bg-red-500/20 border border-red-500/50 rounded p-3">
            <p className="text-red-300 text-sm font-medium">
              ⚠️ Daily costs exceed $5/day limit. Consider optimizing agent
              execution.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
