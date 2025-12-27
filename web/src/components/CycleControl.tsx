'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, Button, Badge } from '@/components/ui'
import { useTriggerCycle } from '@/hooks'
import { Loader2, Play } from 'lucide-react'

const SCHEDULE_OPTIONS = [
  { value: '1h', label: 'Every 1 hour' },
  { value: '3h', label: 'Every 3 hours' },
  { value: '6h', label: 'Every 6 hours' },
  { value: '12h', label: 'Every 12 hours' },
  { value: '24h', label: 'Daily' },
]

export default function CycleControl() {
  const [schedule, setSchedule] = useState('6h')
  const [showConfirm, setShowConfirm] = useState(false)
  const { mutate: triggerCycle, isPending, isSuccess } = useTriggerCycle()

  const handleTrigger = () => {
    triggerCycle()
    setShowConfirm(false)
  }

  return (
    <Card className="col-span-1">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Cycle Control</span>
          <Badge variant={isPending ? 'warning' : 'default'}>
            {isPending ? 'Running' : 'Ready'}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Schedule Selector */}
        <div>
          <label className="text-sm font-medium text-slate-300">
            Auto-Schedule
          </label>
          <select
            value={schedule}
            onChange={(e) => setSchedule(e.target.value)}
            className="w-full mt-2 bg-slate-700 border border-slate-600 rounded px-3 py-2 text-white"
          >
            {SCHEDULE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <p className="text-xs text-slate-400 mt-2">
            Cycles automatically trigger based on schedule
          </p>
        </div>

        {/* Trigger Button */}
        <button
          onClick={() => setShowConfirm(true)}
          disabled={isPending}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 text-white font-semibold py-3 px-4 rounded-lg transition-all flex items-center justify-center gap-2"
        >
          {isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Executing...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Trigger Cycle Now
            </>
          )}
        </button>

        {/* Confirmation Dialog */}
        {showConfirm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 max-w-sm">
              <h3 className="text-lg font-bold text-white mb-4">
                Start Cycle Now?
              </h3>
              <p className="text-slate-300 mb-6">
                This will create 230 tasks and execute them in parallel.
                Cost: ~$1.60
              </p>
              <div className="flex gap-3">
                <button
                  onClick={() => setShowConfirm(false)}
                  className="flex-1 px-4 py-2 border border-slate-600 rounded text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  onClick={handleTrigger}
                  disabled={isPending}
                  className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded font-semibold disabled:bg-slate-600"
                >
                  {isPending ? 'Starting...' : 'Confirm'}
                </button>
              </div>
            </div>
          </div>
        )}

        {isSuccess && (
          <div className="bg-green-500/20 border border-green-500/50 rounded p-3">
            <p className="text-green-300 text-sm font-medium">
              ✅ Cycle triggered successfully!
            </p>
          </div>
        )}

        {/* Info */}
        <div className="bg-slate-700/50 rounded p-3 text-xs text-slate-300">
          <p>
            <strong>230 agents</strong> execute in parallel for optimal
            performance
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
