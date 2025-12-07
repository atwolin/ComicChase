import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { collectionApi } from '@/api/client'
import type { UserCollection } from '@/types'

// 取得使用者收藏列表
export const useCollections = () => {
  return useQuery<UserCollection[]>({
    queryKey: ['collections'],
    queryFn: async () => {
      const data = await collectionApi.getCollections()
      return data.results
    },
  })
}

// 加入收藏
export const useAddCollection = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (seriesId: number) => collectionApi.addCollection(seriesId),
    onSuccess: () => {
      // 確保加入列表後即時更新
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}

// 移除收藏
export const useRemoveCollection = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => collectionApi.removeCollection(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}

