import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getCSRFToken } from '@/lib/django'

interface UserPreferences {
  receive_email: boolean
}

async function fetchPreferences(): Promise<UserPreferences> {
  const response = await fetch('/api/accounts/preferences/')
  if (!response.ok) {
    if (response.status === 401) {
      // Handle unauthenticated if needed, but page should redirect
      throw new Error('Unauthorized')
    }
    throw new Error('Failed to fetch preferences')
  }
  return response.json()
}

async function updatePreferences(
  data: Partial<UserPreferences>
): Promise<UserPreferences> {
  const response = await fetch('/api/accounts/preferences/', {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCSRFToken() || '',
    },
    body: JSON.stringify(data),
  })
  if (!response.ok) throw new Error('Failed to update preferences')
  return response.json()
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
  }
}
