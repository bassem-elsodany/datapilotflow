import { ActionIcon, Button } from '@mantine/core';

export default {
  ActionIcon: ActionIcon.extend({
    defaultProps: {
      radius: 'md',
      variant: 'subtle',
      size: 'sm',
    },
  }),
  Button: Button.extend({
    defaultProps: {
      radius: 'md',
      size: 'sm',
    },
  }),
};
