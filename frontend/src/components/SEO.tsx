import { Helmet } from 'react-helmet-async'

interface SEOProps {
  title: string
  description: string
  keywords?: string[]
  ogImage?: string
  ogType?: 'website' | 'article'
  canonicalUrl?: string
}

const SEO = ({
  title,
  description,
  keywords = [],
  ogImage = '/og-image.jpg',
  ogType = 'website',
  canonicalUrl
}: SEOProps) => {
  const siteTitle = 'Nutritional Psychiatry Database'
  const fullTitle = `${title} | ${siteTitle}`
  const defaultKeywords = [
    'nutritional psychiatry',
    'mental health',
    'brain nutrients',
    'food and mood',
    'nutrition research',
    'mental wellness',
    'diet and depression',
    'brain health',
    'nutritional neuroscience'
  ]

  return (
    <Helmet>
      {/* Basic Meta Tags */}
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      <meta name="keywords" content={[...defaultKeywords, ...keywords].join(', ')} />
      
      {/* Canonical URL */}
      {canonicalUrl && <link rel="canonical" href={canonicalUrl} />}
      
      {/* Open Graph Meta Tags */}
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content={ogType} />
      <meta property="og:image" content={ogImage} />
      <meta property="og:site_name" content={siteTitle} />
      
      {/* Twitter Card Meta Tags */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={description} />
      <meta name="twitter:image" content={ogImage} />
      
      {/* Additional Meta Tags */}
      <meta name="robots" content="index, follow" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <meta name="language" content="English" />
      <meta name="revisit-after" content="7 days" />
      <meta name="author" content="Nutritional Psychiatry Database Team" />
    </Helmet>
  )
}

export default SEO 