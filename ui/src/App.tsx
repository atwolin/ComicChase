import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/react-query'
import { initializeApiClient } from '@/api'
import { AuthProvider } from '@/contexts/AuthContext'

// 初始化 API Client（必須在使用任何 API 前調用）
initializeApiClient()
import { Navbar } from '@/components/Navbar'
import { Home } from '@/pages/Home'
import { SeriesList } from '@/pages/SeriesList'
import { SeriesDetail } from '@/pages/SeriesDetail'
import { Login } from '@/pages/Login'
import { Signup } from '@/pages/Signup'
import { MySubscriptions } from '@/pages/MySubscriptions'
import { Unsubscribe } from '@/pages/Unsubscribe'
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
                <Route path={ROUTES.UNSUBSCRIBE} element={<Unsubscribe />} />
              </Routes>
            </main>
          </div>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}

export default App
