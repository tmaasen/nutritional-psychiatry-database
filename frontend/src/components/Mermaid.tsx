import { useEffect, useRef } from 'react'
import mermaid from 'mermaid'

interface MermaidProps {
  chart: string
}

const Mermaid = ({ chart }: MermaidProps) => {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (ref.current) {
      mermaid.initialize({
        startOnLoad: true,
        theme: 'default',
        securityLevel: 'loose',
        fontFamily: 'inherit',
        flowchart: {
          curve: 'basis',
          padding: 15,
          htmlLabels: true,
          useMaxWidth: true,
        },
        themeVariables: {
          fontFamily: 'inherit',
          fontSize: '16px',
          primaryColor: '#e6f3ff',
          primaryTextColor: '#333',
          primaryBorderColor: '#333',
          lineColor: '#333',
          secondaryColor: '#fff2cc',
          tertiaryColor: '#d5e8d4',
        },
      })
      mermaid.render('mermaid', chart).then(({ svg }) => {
        if (ref.current) {
          ref.current.innerHTML = svg
        }
      })
    }
  }, [chart])

  return <div ref={ref} className="mermaid" />
}

export default Mermaid 