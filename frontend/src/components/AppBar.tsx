import ClearIcon from '@mui/icons-material/Clear';
import GitHubIcon from '@mui/icons-material/GitHub';
import React, {useState} from 'react';
import {AppBar, Toolbar, IconButton, TextField, Button, Typography, Select, MenuItem, InputAdornment} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import {SortByOptions} from '../types/api';

type Props = {
  onSearch: (v: string | null) => void;
  onSortChange: (v: SortByOptions) => void;
  sortBy: SortByOptions;
  openDrawer: () => void;
};

export const TopAppBar: React.FC<Props> = ({
  onSearch,
  onSortChange,
  sortBy,
  openDrawer,
}) => {
  const [textValue, setTextValue] = useState('');
  return (
    <AppBar position="static">
      <Toolbar>
        <IconButton color="inherit" edge="start" onClick={openDrawer}>
          <MenuIcon />
        </IconButton>
        <Typography variant="h6" sx={{flexGrow: 1}}>
          H4ks Games
        </Typography>
        <TextField
          variant="outlined"
          placeholder="Search games..."
          size="small"
          value={textValue}
          onChange={(e) => setTextValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && onSearch(textValue)}
          sx={{borderRadius: 1, flexGrow: 0.5}}
          slotProps={{
            input: {
              endAdornment: textValue && (
                <InputAdornment position='end'>
                  <IconButton
                    onClick={() => setTextValue('')}
                    edge='end'
                    aria-label='clear input'
                    tabIndex={-1}
                    sx={{color: 'text.secondary'}}
                  >
                    <ClearIcon />
                  </IconButton>
                </InputAdornment>
              ),
            },
          }}
        />
        <Button variant="contained" color="primary" sx={{ml: 1}} onClick={() => {
          onSearch(textValue);
        }}>
          Search
        </Button>
        <Select<SortByOptions>
          variant="outlined"
          size='small'
          value={sortBy}
          label="Sort By"
          onChange={(e) => onSortChange(e.target.value as SortByOptions)}
          sx={{ml: 2, borderRadius: 1, flexGrow: 0.1, minWidth: 120}}
        >
          <MenuItem value={"hottest"}>Hot</MenuItem>
          <MenuItem value={"date_added"}>Newest Creation</MenuItem>
          <MenuItem value={"date_modified"}>Newest Edit</MenuItem>
        </Select>
        <IconButton
          color="inherit"
          aria-label="Open in GitHub"
          href="https://github.com/h4ks-com/vibegames"
          target="_blank"
          rel="noopener noreferrer"
        >
          <GitHubIcon />
        </IconButton>
      </Toolbar>
    </AppBar>
  )
};
