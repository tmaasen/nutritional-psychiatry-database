import { useState } from 'react'

interface ImageProps {
  src: string
  alt: string
  width?: number
  height?: number
  className?: string
  priority?: boolean
  loading?: 'lazy' | 'eager'
}

const Image = ({
  src,
  alt,
  width,
  height,
  className = '',
  priority = false,
  loading = 'lazy'
}: ImageProps) => {
  const [isLoading, setIsLoading] = useState(true)

  return (
    <div className={`relative overflow-hidden ${className}`}>
      <img
        src={src}
        alt={alt}
        width={width}
        height={height}
        loading={priority ? 'eager' : loading}
        className={`
          duration-700 ease-in-out
          ${isLoading ? 'scale-110 blur-2xl grayscale' : 'scale-100 blur-0 grayscale-0'}
        `}
        onLoad={() => setIsLoading(false)}
      />
    </div>
  )
}

export default Image 