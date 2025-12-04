import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/react-query'
import { SeriesList } from '@/pages/SeriesList'
import { SeriesDetail } from '@/pages/SeriesDetail'

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <header className="bg-white shadow-sm border-b border-gray-200">
            <div className="container mx-auto px-4 py-4">
              <h1 className="text-2xl font-bold text-gray-900">ComicChase</h1>
            </div>
          </header>
          <main>
            <Routes>
              <Route path="/" element={<SeriesList />} />
              <Route path="/series/:id" element={<SeriesDetail />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App


