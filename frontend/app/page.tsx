'use client'

import { useState } from 'react'
import { ReactFlow, Background, Controls } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import dagre from '@dagrejs/dagre'

const getLayoutedElements = (nodes: any[], edges: any[]) => {
  const g = new dagre.graphlib.Graph()
  g.setGraph({ rankdir: 'TB', nodesep: 50, ranksep: 80 })
  g.setDefaultEdgeLabel(() => ({}))

  nodes.forEach(node => g.setNode(node.id, { width: 120, height: 40 }))
  edges.forEach(edge => g.setEdge(edge.source, edge.target))

  dagre.layout(g)

  const layoutedNodes = nodes.map(node => {
    const pos = g.node(node.id)
    return { ...node, position: { x: pos.x - 60, y: pos.y - 20 } }
  })

  return { nodes: layoutedNodes, edges }
}

export default function Home() {
  const [nodes, setNodes] = useState([])
  const [edges, setEdges] = useState([])
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async () => {
    setLoading(true)
    const parts = url.replace('https://github.com/', '').split('/')
    const owner = parts[0]
    const repo = parts[1]

    const res = await fetch(`http://localhost:8000/repo?owner=${owner}&repo=${repo}`)
    const data = await res.json()

    const rawNodes = data.nodes.slice(0, 100).map((node: any) => ({
      id: node.id,
      data: { label: node.label },
      position: { x: 0, y: 0 },
      style: {
        background: node.type === 'folder' ? '#6366f1' : '#22c55e',
        color: 'white',
        border: 'none',
        borderRadius: '8px',
        fontSize: '11px',
        padding: '6px 10px',
      }
    }))

    const rawEdges = data.edges.slice(0, 200).map((edge: any, index: number) => ({
      id: `e${index}`,
      source: edge.source,
      target: edge.target,
    }))

    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(rawNodes, rawEdges)

    setNodes(layoutedNodes)
    setEdges(layoutedEdges)
    setLoading(false)
  }

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '16px', background: '#0f172a', display: 'flex', gap: '8px' }}>
        <input
          style={{ flex: 1, padding: '8px 12px', borderRadius: '8px', border: 'none', fontSize: '14px' }}
          placeholder="Paste a GitHub repo URL e.g. https://github.com/tiangolo/fastapi"
          value={url}
          onChange={e => setUrl(e.target.value)}
        />
        <button
          onClick={handleSubmit}
          style={{ padding: '8px 20px', background: '#6366f1', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '14px' }}
        >
          {loading ? 'Loading...' : 'Visualize'}
        </button>
      </div>
      <div style={{ flex: 1 }}>
        <ReactFlow nodes={nodes} edges={edges} fitView>
          <Background />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  )
}