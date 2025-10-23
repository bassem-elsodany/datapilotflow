import { NavLink } from 'react-router-dom';
import { Anchor, Stack, Text, Title } from '@mantine/core';
import { Page } from '@/components/page';
import { UnderlineShape } from '@/components/underline-shape';
import { paths } from '@/routes';
import { LoginForm } from './login-form';

export default function LoginPage() {
  return (
    <Page title="Login">
      <Stack gap="xl">
        <Stack>
          <Title order={2}>
            Welcome to{' '}
            <Text fz="inherit" fw="inherit" component="span" pos="relative">
              DataPilotFlow
              <UnderlineShape
                c="blue"
                left="0"
                pos="absolute"
                h="0.625rem"
                bottom="-1rem"
                w="7rem"
              />
            </Text>{' '}
            Dashboard
          </Title>
          <Text fz="sm" c="dimmed">
            Sign in to access the RAG management system and RAG tools.
          </Text>
        </Stack>

        <LoginForm />

        <Text fz="sm" c="dimmed">
          Don&apos;t have an account?{' '}
          <Anchor fz="inherit" component={NavLink} to={paths.auth.register}>
            Contact your administrator to get an account
          </Anchor>
        </Text>
      </Stack>
    </Page>
  );
}
