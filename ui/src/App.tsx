import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/react-query'
import '@/lib/api-client' // 配置 API client (CSRF token 等)
import { AuthProvider } from '@/contexts/AuthContext'
import { Navbar } from '@/components/Navbar'
import { Home } from '@/pages/Home'
import { SeriesList } from '@/pages/SeriesList'
import { SeriesDetail } from '@/pages/SeriesDetail'
import { Login } from '@/pages/Login'
import { Signup } from '@/pages/Signup'
import { MySubscriptions } from '@/pages/MySubscriptions'
import { ROUTES } from '@/constants/routes'

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <div className="min-h-screen">
            <Navbar />
            <main>
              <Routes>
                <Route path={ROUTES.HOME} element={<Home />} />
                <Route path={ROUTES.SERIES_LIST} element={<SeriesList />} />
                <Route
                  path={ROUTES.SERIES_DETAIL_PATTERN}
                  element={<SeriesDetail />}
                />
                <Route path={ROUTES.LOGIN} element={<Login />} />
                <Route path={ROUTES.SIGNUP} element={<Signup />} />
                <Route
                  path={ROUTES.MY_SUBSCRIPTIONS}
                  element={<MySubscriptions />}
                />
              </Routes>
            </main>
          </div>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
