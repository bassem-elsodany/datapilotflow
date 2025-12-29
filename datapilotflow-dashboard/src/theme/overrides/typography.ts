import { Text, Title } from '@mantine/core';

export default {
  Text: Text.extend({
    defaultProps: {
      size: 'sm',
    },
  }),
  Title: Title.extend({
    defaultProps: {
      // Title sizes are controlled by theme.headings and order; keep defaults here
    },
  }),
};


