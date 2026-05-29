import { DefaultTheme } from 'react-native-paper';

export const colors = {
  primary: '#6c5ce7',
  secondary: '#00b894',
  danger: '#e17055',
  dark: '#2d3436',
  mediumGray: '#636e72',
  lightGray: '#b2bec3',
  background: '#f0f2f5',
  surface: '#ffffff',
  border: '#dfe6e9',
};

export const paperTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    primary: colors.primary,
    accent: colors.secondary,
    background: colors.background,
    surface: colors.surface,
    text: colors.dark,
    placeholder: colors.lightGray,
    disabled: colors.border,
    error: colors.danger,
  },
};
