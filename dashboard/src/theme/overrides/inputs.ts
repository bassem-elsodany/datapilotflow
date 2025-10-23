import { InputBase, PasswordInput } from '@mantine/core';

export default {
  InputBase: InputBase.extend({
    defaultProps: {
      radius: 'md',
      size: 'sm',
    },
  }),
  PasswordInput: PasswordInput.extend({
    defaultProps: {
      radius: 'md',
      size: 'sm',
    },
  }),
};
