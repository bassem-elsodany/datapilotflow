import { PiArrowLeft as GoBackIcon } from 'react-icons/pi';
import { Outlet, useNavigate } from 'react-router-dom';
import { Box, Button, Center, Flex, Image, SimpleGrid, Text, Title } from '@mantine/core';
import demoImg from '@/assets/app-demo.webp';
import { Logo } from '@/components/logo';

export function AuthLayout() {
  const navigate = useNavigate();

  return (
    <SimpleGrid mih="100vh" p="md" cols={{ base: 1, lg: 2 }}>
      <Flex direction="column" align="flex-start">
        <Button
          c="inherit"
          variant="subtle"
          leftSection={<GoBackIcon size="1rem" />}
          onClick={() => navigate(-1)}
        >
          Go back
        </Button>

        <Center flex={1} w="100%">
          <Box px="md">
            <Box>
              <Logo 
                height="3rem" 
                display="block"
              />
            </Box>
            <Outlet />
          </Box>
        </Center>
      </Flex>

      <Center
        ta="center"
        p="4rem"
        bg="var(--mantine-color-default-hover)"
        display={{ base: 'none', lg: 'flex' }}
        style={{ borderRadius: 'var(--mantine-radius-md)' }}
      >
        <Box maw="40rem">
          <Title order={2}>AI-Powered RAG Management & Knowledge System</Title>
          <Text my="lg" c="dimmed">
            Upload documents, configure RAG injections, and have intelligent conversations with your knowledge sources. 
            DataPilotFlow helps you build and manage comprehensive RAG systems with advanced AI capabilities.
          </Text>

          <Image src={demoImg} alt="Demo" />
        </Box>
      </Center>
    </SimpleGrid>
  );
}
