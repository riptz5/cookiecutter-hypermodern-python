'use client'

import { Card, CardContent } from '@/components/ui'
import { TrendingDown, TrendingUp, Minus } from 'lucide-react'
import { LineChart, Line, ResponsiveContainer } from 'recharts'

interface MetricsCardProps {
  label: string
  value: number
  target: number
  trend?: 'up' | 'down' | 'stable'
  unit?: string
  sparklineData?: Array<{ value: number }>
  isLoading?: boolean
}

export default function MetricsCard({
  label,
  value,
  target,
  trend = 'stable',
  unit = '',
  sparklineData = [],
  isLoading = false,
}: MetricsCardProps) {
  // Calculate progress
  const progress = Math.min((value / target) * 100, 100)
  const diff = value - target
  const isMet = value >= target

  // Determine color based on progress
  const getColor = (pct: number) => {
    if (pct >= 100) return 'text-green-400'
    if (pct >= 80) return 'text-blue-400'
    if (pct >= 50) return 'text-yellow-400'
    return 'text-red-400'
  }

  // Sparkline mock data
  const mockSparkline = [
    { value: value * 0.9 },
    { value: value * 0.92 },
    { value: value * 0.95 },
    { value: value * 0.98 },
    { value: value },
  ]

  return (
    <Card className="h-full">
      <CardContent className="p-4 space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-slate-400">{label}</p>
            <p className={`text-2xl font-bold ${getColor(progress)}`}>
              {isLoading ? (
                <span className="animate-pulse">---</span>
              ) : (
                <>
                  {value.toFixed(2)}
                  {unit && <span className="text-sm ml-1">{unit}</span>}
                </>
              )}
            </p>
          </div>

          {/* Trend Indicator */}
          <div className="flex items-center gap-1">
            {trend === 'up' && (
              <TrendingUp className="w-5 h-5 text-green-400" />
            )}
            {trend === 'down' && (
              <TrendingDown className="w-5 h-5 text-red-400" />
            )}
            {trend === 'stable' && (
              <Minus className="w-5 h-5 text-slate-400" />
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">Progress</span>
            <span className={`${getColor(progress)} font-medium`}>
              {progress.toFixed(0)}%
            </span>
          </div>
          <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all ${
                progress >= 100
                  ? 'bg-green-500'
                  : progress >= 80
                  ? 'bg-blue-500'
                  : progress >= 50
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              }`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Target Info */}
        <div className="flex justify-between text-xs text-slate-400">
          <span>Target: {target.toFixed(2)}{unit && ` ${unit}`}</span>
          <span>
            {diff >= 0 ? '+' : ''}{diff.toFixed(2)} {unit}
          </span>
        </div>

        {/* Mini Sparkline */}
        {sparklineData.length > 0 || mockSparkline.length > 0 && (
          <div className="h-12 -mx-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={sparklineData.length > 0 ? sparklineData : mockSparkline}>
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke={getColor(progress).replace('text-', '#').split('-')[0]}
                  dot={false}
                  strokeWidth={2}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Status Badge */}
        {isMet ? (
          <div className="bg-green-500/20 border border-green-500/50 rounded px-3 py-2 text-center">
            <p className="text-xs font-medium text-green-300">✅ Target Met</p>
          </div>
        ) : (
          <div className="bg-yellow-500/20 border border-yellow-500/50 rounded px-3 py-2 text-center">
            <p className="text-xs font-medium text-yellow-300">
              ⏳ {(target - value).toFixed(2)} to target
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
