import { deepPurple, purple, green, blue, lightGreen, lime, grey, yellow, amber, red, orange, cyan, blueGrey } from '@mui/material/colors';
import { createTheme } from '@mui/material/styles';

export const lightTheme = createTheme({
  palette: {
    mode: 'light',
    primary: lime,
    secondary: red,
  },
});

export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: orange,
    secondary: orange,
  },
});
