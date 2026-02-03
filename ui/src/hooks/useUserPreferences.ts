import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  accountsPreferencesRetrieve,
  accountsPreferencesPartialUpdate,
} from '@/api'
import type { UserPreference } from '@/api'

async function fetchPreferences() {
  const { data } = await accountsPreferencesRetrieve()
  return data as UserPreference
}

async function updatePreferences(data: Partial<UserPreference>) {
  const { data: responseData } = await accountsPreferencesPartialUpdate({
    body: data,
  })
  return responseData as UserPreference
}

export function useUserPreferences() {
  const queryClient = useQueryClient()

  const query = useQuery({
    queryKey: ['user-preferences'],
    queryFn: fetchPreferences,
    retry: false,
  })

  const mutation = useMutation({
    mutationFn: updatePreferences,
    onSuccess: newData => {
      queryClient.setQueryData(['user-preferences'], newData)
    },
  })

  return {
    preferences: query.data,
    isLoading: query.isLoading,
    update: mutation.mutate,
    updateAsync: mutation.mutateAsync,
    isUpdating: mutation.isPending,
    isError: query.isError,
  }
}
