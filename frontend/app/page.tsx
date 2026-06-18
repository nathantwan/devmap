'use client'

import { useEffect, useState } from 'react'
import { ReactFlow, Background, Controls } from '@xyflow/react'
import '@xyflow/react/dist/style.css'

export default function Home() {
  const [nodes, setNodes] = useState([])
  const [edges, setEdges] = useState([])

  useEffect(() => {
    fetch('http://localhost:8000/repo?owner=tiangolo&repo=fastapi')
      .then(res => res.json())
      .then(data => {
        const flowNodes = data.nodes.slice(0, 50).map((node: any, index: number) => ({
          id: node.id,
          data: { label: node.label },
          position: { x: (index % 10) * 150, y: Math.floor(index / 10) * 100 },
          style: {
            background: node.type === 'folder' ? '#6366f1' : '#22c55e',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '11px',
            padding: '6px 10px',
          }
        }))

        const flowEdges = data.edges.slice(0, 100).map((edge: any, index: number) => ({
          id: `e${index}`,
          source: edge.source,
          target: edge.target,
        }))

        setNodes(flowNodes)
        setEdges(flowEdges)
      })
  }, [])

  return (
    <div style={{ width: '100vw', height: '100vh' }}>
      <ReactFlow nodes={nodes} edges={edges} fitView>
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  )
}