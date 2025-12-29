import { forwardRef, ReactNode } from 'react';
import { Helmet } from 'react-helmet-async';
import { Box, BoxProps } from '@mantine/core';
import { app } from '@/config';

interface PageProps extends BoxProps {
  children: ReactNode;
  meta?: ReactNode;
  title: string;
}
export const Page = forwardRef<HTMLDivElement, PageProps>(
  ({ children, title = '', meta, ...other }, ref) => {
    return (
      <>
        <Helmet>
          <title>{`${title} | ${app.name}`}</title>
          {meta}
        </Helmet>

        <Box ref={ref} {...other}>
          {children}
        </Box>
      </>
    );
  }
);
