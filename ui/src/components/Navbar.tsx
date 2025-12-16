import { Link } from 'react-router-dom'
import { ROUTES } from '@/constants/routes'

// 導覽列元件
export const Navbar = () => {
  return (
    <nav className="bg-white/80 backdrop-blur-md shadow-md border-b border-gray-200 sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link
            to={ROUTES.HOME}
            className="flex items-center gap-3 transition-transform duration-300 hover:scale-105 origin-left"
          >
            <img
              src="/logo.png"
              alt="ComicChase"
              className="h-14 w-auto object-contain"
              onError={e => {
                const target = e.target as HTMLImageElement
                target.style.display = 'none'
              }}
            />
            {/* 文字 */}
            <span className="text-2xl font-bold bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              ComicChase
            </span>
          </Link>
        </div>
      </div>
    </nav>
  )
}
