import React from 'react';
import {AppBar, Toolbar, IconButton, TextField, Button, Typography} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';

type Props = {
  searchTerm: string;
  onSearchChange: (v: string) => void;
  onSearch: () => void;
  onSortChange: () => void;
  sortBy: string;
  openDrawer: () => void;
};

export const TopAppBar: React.FC<Props> = ({
  searchTerm,
  onSearchChange,
  onSearch,
  onSortChange,
  sortBy,
  openDrawer,
}) => (
  <AppBar position="static">
    <Toolbar>
      <IconButton color="inherit" edge="start" onClick={openDrawer}>
        <MenuIcon />
      </IconButton>
      <Typography variant="h6" sx={{flexGrow: 1}}>
        Gaming Projects
      </Typography>
      <TextField
        variant="outlined"
        placeholder="Search games..."
        size="small"
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && onSearch()}
        sx={{backgroundColor: 'white', borderRadius: 1}}
      />
      <Button variant="contained" color="primary" sx={{ml: 1}} onClick={onSearch}>
        Search
      </Button>
      <Button variant="outlined" color="primary" sx={{ml: 1}} onClick={onSortChange}>
        Sort: {sortBy}
      </Button>
    </Toolbar>
  </AppBar>
);
