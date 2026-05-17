'use client';

import { useCallback, useEffect, useState } from 'react';
import { API_BASE } from '@/lib/api';
import type { Telemetry } from '@/types/telemetry';

export function useTelemetry(enabled: boolean, pollMs = 3000) {
  const [data, setData] = useState<Telemetry | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTelemetry = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/telemetry`, {
        cache: 'no-store',
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
      setError(null);
    } catch (e) {
      setError(
        e instanceof Error ? e.message : 'Could not reach telemetry endpoint'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!enabled) return;
    fetchTelemetry();
    const id = setInterval(fetchTelemetry, pollMs);
    return () => clearInterval(id);
  }, [enabled, pollMs, fetchTelemetry]);

  return { data, loading, error, refresh: fetchTelemetry };
}
