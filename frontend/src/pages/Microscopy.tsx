import { FormEvent, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { FlocDensity, MicroscopyBatch, Pond } from '../types'

function todayLocal() {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 10)
}

function nowLocal() {
  const d = new Date()
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset())
  return d.toISOString().slice(0, 16)
}

const DENSITY_LABEL: Record<FlocDensity, string> = {
  sparse: '稀',
  medium: '中',
  dense: '密',
}

const emptyBatch = {
  pondId: 0,
  inspectedOn: todayLocal(),
  chiefInspector: '水质技术员',
}

function BatchCard({
  batch,
  ponds,
  onChange,
}: {
  batch: MicroscopyBatch
  ponds: Pond[]
  onChange: () => Promise<void>
}) {
  const [viewNo, setViewNo] = useState(
    batch.views.reduce((m, v) => Math.max(m, v.viewNo), 0) + 1,
  )
  const [flocDensity, setFlocDensity] = useState<FlocDensity>('medium')
  const [observedAt, setObservedAt] = useState(nowLocal())
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const sealed = batch.sealedAt !== null
  const pond = ponds.find((p) => p.id === batch.pondId)
  const pondLabel = pond ? `${pond.pondCode} · ${pond.species}` : `#${batch.pondId}`

  async function addView(e: FormEvent) {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await api(`/api/microscopy-batches/${batch.id}/views`, {
        method: 'POST',
        body: JSON.stringify({
          viewNo,
          flocDensity,
          observedAt: new Date(observedAt).toISOString(),
        }),
      })
      await onChange()
      setViewNo((n) => n + 1)
      setObservedAt(nowLocal())
    } catch (err) {
      setError(err instanceof Error ? err.message : '追加视野失败')
    } finally {
      setBusy(false)
    }
  }

  async function seal() {
    setError('')
    setBusy(true)
    try {
      await api(`/api/microscopy-batches/${batch.id}/seal`, { method: 'POST' })
      await onChange()
    } catch (err) {
      setError(err instanceof Error ? err.message : '封检失败')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="panel batch-card">
      <div className="batch-head">
        <div>
          <strong>批次 #{batch.id}</strong>
          <span className="muted">
            {' '}
            塘口 {pondLabel} · 开检日 {batch.inspectedOn}（东八区） · 主检人{' '}
            {batch.chiefInspector}
          </span>
        </div>
        {sealed ? (
          <span className="badge sealed">已封检 {new Date(batch.sealedAt!).toLocaleString()}</span>
        ) : (
          <span className="badge open">未封检</span>
        )}
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>视野序号</th>
              <th>絮团密度</th>
              <th>观察时刻</th>
            </tr>
          </thead>
          <tbody>
            {batch.views.length === 0 ? (
              <tr>
                <td colSpan={3} className="muted">
                  暂无视野条目
                </td>
              </tr>
            ) : (
              batch.views.map((v) => (
                <tr key={v.id}>
                  <td>{v.viewNo}</td>
                  <td>{DENSITY_LABEL[v.flocDensity]}</td>
                  <td>{new Date(v.observedAt).toLocaleString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {!sealed && (
        <>
          <form className="form-inline" onSubmit={addView}>
            <label>
              视野序号
              <input
                type="number"
                min={1}
                value={viewNo}
                onChange={(e) => setViewNo(Number(e.target.value))}
                required
              />
            </label>
            <label>
              絮团密度
              <select
                value={flocDensity}
                onChange={(e) => setFlocDensity(e.target.value as FlocDensity)}
              >
                <option value="sparse">稀</option>
                <option value="medium">中</option>
                <option value="dense">密</option>
              </select>
            </label>
            <label>
              观察时刻
              <input
                type="datetime-local"
                value={observedAt}
                onChange={(e) => setObservedAt(e.target.value)}
                required
              />
            </label>
            <button type="submit" className="btn" disabled={busy}>
              追加视野
            </button>
            <button type="button" className="btn primary" onClick={seal} disabled={busy}>
              封检
            </button>
          </form>
          <p className="muted">
            封检规则：至少 3 个视野，且不得全部为「密」；不满足时返回 409，封检时刻保持为空。封检后不可再追加视野。
          </p>
        </>
      )}
      {error && <div className="error">{error}</div>}
    </div>
  )
}

export default function Microscopy() {
  const [ponds, setPonds] = useState<Pond[]>([])
  const [rows, setRows] = useState<MicroscopyBatch[]>([])
  const [form, setForm] = useState(emptyBatch)
  const [error, setError] = useState('')

  async function load() {
    const [ps, bs] = await Promise.all([
      api<Pond[]>('/api/ponds'),
      api<MicroscopyBatch[]>('/api/microscopy-batches'),
    ])
    setPonds(ps)
    setRows(bs)
    if (!form.pondId && ps[0]) {
      setForm((f) => ({ ...f, pondId: ps[0].id }))
    }
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
  }, [])

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    try {
      await api('/api/microscopy-batches', {
        method: 'POST',
        body: JSON.stringify(form),
      })
      setForm((f) => ({ ...emptyBatch, pondId: f.pondId, inspectedOn: todayLocal() }))
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '新建批次失败')
    }
  }

  return (
    <div>
      <header className="page-header">
        <h1>絮团镜检</h1>
        <p className="muted">
          批次挂塘口，镜检结果决定能否继续投喂。同塘开检日（东八区）唯一；未封批次内视野序号唯一。
        </p>
      </header>
      {error && <div className="error">{error}</div>}

      <form className="panel form-grid" onSubmit={onSubmit}>
        <label>
          所属塘口
          <select
            value={form.pondId}
            onChange={(e) => setForm({ ...form, pondId: Number(e.target.value) })}
            required
          >
            {ponds.map((p) => (
              <option key={p.id} value={p.id}>
                {p.pondCode} · {p.species}
              </option>
            ))}
          </select>
        </label>
        <label>
          开检日（东八区）
          <input
            type="date"
            value={form.inspectedOn}
            onChange={(e) => setForm({ ...form, inspectedOn: e.target.value })}
            required
          />
        </label>
        <label>
          主检人
          <input
            value={form.chiefInspector}
            onChange={(e) => setForm({ ...form, chiefInspector: e.target.value })}
            required
          />
        </label>
        <button type="submit" className="btn primary">
          新建镜检批次
        </button>
      </form>

      {rows.length === 0 ? (
        <div className="panel muted">
          暂无镜检批次。封检规则：每批次至少 3 个视野且密度不得全为「密」方可封检；封检前该塘口禁止新建投喂。
        </div>
      ) : (
        rows.map((b) => <BatchCard key={b.id} batch={b} ponds={ponds} onChange={load} />)
      )}
    </div>
  )
}
