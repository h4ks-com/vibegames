import {createTheme} from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark', // Dark theme
    primary: {
      main: '#2979ff', // blue accent
    },
    secondary: {
      main: '#ff4081',
    },
    background: {
      default: '#121212',
      paper: '#1e1e1e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    // Optionally add more component customizations here.
  },
});

export default theme;
