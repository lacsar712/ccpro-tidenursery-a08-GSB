import { FormEvent, useEffect, useState } from 'react'
import { api } from '../api/client'
import type { DensityLevel, MicroscopyBatch, Pond } from '../types'

const DENSITY_LABEL: Record<DensityLevel, string> = {
  sparse: '稀',
  medium: '中',
  dense: '密',
}

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

type FieldForm = {
  viewSeq: number
  density: DensityLevel
  observedAt: string
}

export default function Microscopy() {
  const [ponds, setPonds] = useState<Pond[]>([])
  const [batches, setBatches] = useState<MicroscopyBatch[]>([])
  const [form, setForm] = useState({
    pondId: 0,
    openedOn: todayLocal(),
    chiefInspector: '场长',
  })
  const [fieldForms, setFieldForms] = useState<Record<number, FieldForm>>({})
  const [error, setError] = useState('')

  async function load() {
    const [ps, bs] = await Promise.all([
      api<Pond[]>('/api/ponds'),
      api<MicroscopyBatch[]>('/api/microscopy-batches'),
    ])
    setPonds(ps)
    setBatches(bs)
    if (!form.pondId && ps[0]) {
      setForm((f) => ({ ...f, pondId: ps[0].id }))
    }
    // 为每个未封批次准备默认视野表单
    setFieldForms((prev) => {
      const next: Record<number, FieldForm> = {}
      for (const b of bs) {
        if (b.closedAt) continue
        const used = new Set(b.fields.map((x) => x.viewSeq))
        let nextSeq = 1
        while (used.has(nextSeq)) nextSeq += 1
        const old = prev[b.id]
        // 保留用户输入的序号，但若已被占用则跳到下一个未用序号
        const seq = old && old.viewSeq > 0 && !used.has(old.viewSeq) ? old.viewSeq : nextSeq
        next[b.id] = old
          ? { ...old, viewSeq: seq }
          : { viewSeq: nextSeq, density: 'medium', observedAt: nowLocal() }
      }
      return next
    })
  }

  useEffect(() => {
    load().catch((e) => setError(e.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function createBatch(e: FormEvent) {
    e.preventDefault()
    setError('')
    try {
      await api('/api/microscopy-batches', {
        method: 'POST',
        body: JSON.stringify(form),
      })
      setForm((f) => ({ ...f, openedOn: todayLocal() }))
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '开检失败')
    }
  }

  async function addField(batchId: number) {
    setError('')
    const ff = fieldForms[batchId]
    if (!ff) return
    try {
      await api(`/api/microscopy-batches/${batchId}/fields`, {
        method: 'POST',
        body: JSON.stringify({
          viewSeq: ff.viewSeq,
          density: ff.density,
          observedAt: new Date(ff.observedAt).toISOString(),
        }),
      })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '追加视野失败')
    }
  }

  async function closeBatch(batchId: number) {
    setError('')
    try {
      await api(`/api/microscopy-batches/${batchId}/close`, { method: 'POST' })
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : '封检失败')
    }
  }

  const pondLabel = (id: number) => {
    const p = ponds.find((x) => x.id === id)
    return p ? `${p.pondCode} · ${p.species}` : `#${id}`
  }

  const setFieldForm = (batchId: number, patch: Partial<FieldForm>) =>
    setFieldForms((prev) => ({ ...prev, [batchId]: { ...prev[batchId], ...patch } }))

  return (
    <div>
      <header className="page-header">
        <h1>絮团镜检</h1>
        <p className="muted">
          批次挂塘口，镜检条目决定能否继续投喂。封检规则：至少 3 个视野，且不得全为「密」；
          未封检批次期间该塘口禁止新建投喂。
        </p>
      </header>
      {error && <div className="error">{error}</div>}

      <form className="panel form-grid" onSubmit={createBatch}>
        <label>
          塘口
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
            value={form.openedOn}
            onChange={(e) => setForm({ ...form, openedOn: e.target.value })}
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
          开检（新建批次）
        </button>
      </form>

      <div className="batch-list">
        {batches.map((b) => {
          const closed = b.closedAt !== null
          const ff = fieldForms[b.id]
          return (
            <div key={b.id} className="panel batch-card">
              <div className="batch-head">
                <div>
                  <strong>批次 #{b.id}</strong>
                  <span className="muted"> · {pondLabel(b.pondId)}</span>
                </div>
                <span className={`badge ${closed ? 'stocked' : 'quarantine'}`}>
                  {closed ? `已封检 ${new Date(b.closedAt as string).toLocaleString()}` : '未封检'}
                </span>
              </div>
              <div className="hint">
                开检日（东八区）：{b.openedOn} ｜ 主检人：{b.chiefInspector} ｜ 视野数：
                {b.fields.length}
              </div>

              <div className="table-wrap batch-fields">
                <table>
                  <thead>
                    <tr>
                      <th>视野序号</th>
                      <th>絮团密度</th>
                      <th>观察时刻</th>
                    </tr>
                  </thead>
                  <tbody>
                    {b.fields
                      .slice()
                      .sort((a, c) => a.viewSeq - c.viewSeq)
                      .map((f) => (
                        <tr key={f.id}>
                          <td>{f.viewSeq}</td>
                          <td>{DENSITY_LABEL[f.density]}</td>
                          <td>{new Date(f.observedAt).toLocaleString()}</td>
                        </tr>
                      ))}
                    {b.fields.length === 0 && (
                      <tr>
                        <td colSpan={3} className="muted">
                          尚无视野条目
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {!closed && ff && (
                <div className="field-add">
                  <label>
                    视野序号
                    <input
                      type="number"
                      min={1}
                      value={ff.viewSeq}
                      onChange={(e) =>
                        setFieldForm(b.id, { viewSeq: Number(e.target.value) })
                      }
                    />
                  </label>
                  <label>
                    密度
                    <select
                      value={ff.density}
                      onChange={(e) =>
                        setFieldForm(b.id, { density: e.target.value as DensityLevel })
                      }
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
                      value={ff.observedAt}
                      onChange={(e) => setFieldForm(b.id, { observedAt: e.target.value })}
                    />
                  </label>
                  <button type="button" className="btn ghost" onClick={() => addField(b.id)}>
                    追加视野
                  </button>
                  <button type="button" className="btn primary" onClick={() => closeBatch(b.id)}>
                    封检
                  </button>
                </div>
              )}
            </div>
          )
        })}
        {batches.length === 0 && <p className="muted">暂无镜检批次</p>}
      </div>
    </div>
  )
}
