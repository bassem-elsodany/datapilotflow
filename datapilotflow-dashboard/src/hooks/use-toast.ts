import { notifications } from '@mantine/notifications';

export function useToast() {
  return {
    toast: ({ title, description, variant = 'default' }: { title: string; description?: string; variant?: 'default' | 'destructive' }) => {
      notifications.show({
        title,
        message: description,
        color: variant === 'destructive' ? 'red' : 'blue',
      });
    },
  };
}
