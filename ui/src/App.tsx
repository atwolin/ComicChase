import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/react-query'
import { Navbar } from '@/components/Navbar'
import { Home } from '@/pages/Home'
import { SeriesList } from '@/pages/SeriesList'
import { SeriesDetail } from '@/pages/SeriesDetail'

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen">
          <Navbar />
          <main>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/series" element={<SeriesList />} />
              <Route path="/series/:id" element={<SeriesDetail />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App

