import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { collectionApi } from '@/api/client'
import type { UserCollection } from '@/types'

export const useCollections = () => {
  return useQuery({
    queryKey: ['collections'],
    queryFn: async () => {
      const data = await collectionApi.getCollections()
      return data.results
    },
  })
}

export const useAddCollection = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (seriesId: number) => collectionApi.addCollection(seriesId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}

export const useRemoveCollection = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => collectionApi.removeCollection(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
  })
}

