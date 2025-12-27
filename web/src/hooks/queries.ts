'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api, metricsApi, costApi, logsApi, orchestratorApi, configApi } from '@/lib/api'
import { useToast } from './use-toast'

// ============================================================================
// METRICS QUERIES
// ============================================================================

export function useMetricsCurrent() {
  return useQuery({
    queryKey: ['metrics', 'current'],
    queryFn: metricsApi.getCurrentMetrics,
    refetchInterval: 5000,
    staleTime: 3000,
  })
}

export function useMetricsHistory(days: number = 30) {
  return useQuery({
    queryKey: ['metrics', 'history', days],
    queryFn: () => metricsApi.getMetricsHistory(days),
    refetchInterval: 30000,
    staleTime: 20000,
  })
}

// ============================================================================
// COSTS QUERIES
// ============================================================================

export function useCostData() {
  return useQuery({
    queryKey: ['costs', 'current'],
    queryFn: costApi.getCostData,
    refetchInterval: 10000,
    staleTime: 8000,
  })
}

export function useCostProjection(cycleCount: number = 1) {
  return useQuery({
    queryKey: ['costs', 'projection', cycleCount],
    queryFn: () => costApi.getMonthlyProjection(),
    refetchInterval: 60000,
    staleTime: 50000,
  })
}

// ============================================================================
// CYCLES QUERIES
// ============================================================================

export function useCyclesList(limit: number = 10) {
  return useQuery({
    queryKey: ['cycles', 'list', limit],
    queryFn: orchestratorApi.getAllCycles,
    refetchInterval: 10000,
    staleTime: 5000,
  })
}

export function useCycleStatus(cycleId: string) {
  return useQuery({
    queryKey: ['cycles', 'status', cycleId],
    queryFn: () => orchestratorApi.getCycleStatus(cycleId),
    refetchInterval: 5000,
    staleTime: 3000,
    enabled: !!cycleId,
  })
}

// ============================================================================
// LOGS QUERIES
// ============================================================================

export function useLogsRecent(limit: number = 50) {
  return useQuery({
    queryKey: ['logs', 'recent', limit],
    queryFn: () => logsApi.getRecentLogs(limit),
    refetchInterval: 5000,
    staleTime: 3000,
  })
}

// ============================================================================
// CONFIGURATION QUERIES
// ============================================================================

export function useConfig() {
  return useQuery({
    queryKey: ['config'],
    queryFn: configApi.getConfig,
    staleTime: Infinity,
  })
}

// ============================================================================
// MUTATIONS
// ============================================================================

export function useTriggerCycle() {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: orchestratorApi.triggerCycle,
    onSuccess: (data) => {
      toast({
        title: '✅ Cycle Started',
        description: `Cycle ${data.cycleId} started successfully`,
        variant: 'success',
      })

      // Refetch cycles list
      queryClient.invalidateQueries({ queryKey: ['cycles'] })
      queryClient.invalidateQueries({ queryKey: ['metrics'] })
    },
    onError: (error) => {
      toast({
        title: '❌ Failed to Start Cycle',
        description: String(error),
        variant: 'destructive',
      })
    },
  })
}

export function useUpdateConfig() {
  const { toast } = useToast()
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (config: Record<string, any>) => configApi.updateConfig(config),
    onSuccess: () => {
      toast({
        title: '✅ Config Updated',
        description: 'Configuration saved successfully',
        variant: 'success',
      })

      queryClient.invalidateQueries({ queryKey: ['config'] })
    },
    onError: (error) => {
      toast({
        title: '❌ Failed to Update Config',
        description: String(error),
        variant: 'destructive',
      })
    },
  })
}

// ============================================================================
// REAL-TIME STREAMING HOOKS
// ============================================================================

export function useLogsStream(onLog: (log: any) => void) {
  const { toast } = useToast()

  return {
    subscribe: () => {
      return logsApi.streamLogs(
        onLog,
        (error) => {
          toast({
            title: '⚠️ Log Connection Lost',
            description: 'Attempting to reconnect...',
            variant: 'destructive',
          })
        }
      )
    },
  }
}

// ============================================================================
// COMBINED HOOKS
// ============================================================================

export function useDashboardData() {
  const metrics = useMetricsCurrent()
  const costs = useCostData()
  const cycles = useCyclesList(10)
  const logs = useLogsRecent(50)

  const isLoading = metrics.isLoading || costs.isLoading || cycles.isLoading
  const isError = metrics.isError || costs.isError || cycles.isError

  return {
    metrics: metrics.data,
    costs: costs.data,
    cycles: cycles.data,
    logs: logs.data,
    isLoading,
    isError,
    refetch: () => {
      metrics.refetch()
      costs.refetch()
      cycles.refetch()
      logs.refetch()
    },
  }
}
