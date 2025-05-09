import GitHubIcon from '@mui/icons-material/GitHub';
import React, { useState } from 'react';
import { AppBar, Toolbar, IconButton, TextField, Button, Typography, Select, MenuItem, useTheme, useMediaQuery } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import { SortByOptions } from '../types/api';
import { ClearAdorment } from './ClearAdorment';

type Props = {
  initialSearch: string | null;
  onSearch: (v: string | null) => void;
  onSortChange: (v: SortByOptions) => void;
  sortBy: SortByOptions;
  openDrawer: () => void;
};

export const TopAppBar: React.FC<Props> = ({
  initialSearch,
  onSearch,
  onSortChange,
  sortBy,
  openDrawer,
}) => {
  const [textValue, setTextValue] = useState(initialSearch || '');
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  const handleSearch = (query: string) => {
    onSearch(query);
    const url = new URL(window.location.href);
    if (query) {
      url.searchParams.set('search', query);
    } else {
      url.searchParams.delete('search');
    }
    window.history.pushState({}, '', url.toString());
  };

  const handleSort = (value: SortByOptions) => {
    onSortChange(value);
    const url = new URL(window.location.href);
    url.searchParams.set('sort', value);
    window.history.pushState({}, '', url.toString());
  };

  return (
    <AppBar position="static">
      <Toolbar>
        {!isMobile && (
          <IconButton color="inherit" edge="start" onClick={openDrawer}>
            <MenuIcon />
          </IconButton>
        )}
        {!isMobile && (
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            H4ks Games
          </Typography>
        )}
        <TextField
          variant="outlined"
          placeholder="Search games..."
          size="small"
          value={textValue}
          onChange={(e) => setTextValue(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch(textValue)}
          sx={{
            borderRadius: 1,
            flexGrow: isMobile ? 1 : 0,
            width: isMobile ? 'auto' : '40%',
          }}
          slotProps={{
            input: {
              endAdornment: textValue && (
                <ClearAdorment
                  onClick={() => setTextValue('')}
                />
              ),
            },
          }}
        />
        <Button variant="contained" color="primary" sx={{ ml: 1 }} onClick={() => {
          handleSearch(textValue);
        }}>
          Search
        </Button>
        {!isMobile && (
          <Select<SortByOptions>
            variant="outlined"
            size='small'
            value={sortBy}
            label="Sort By"
            onChange={(e) => handleSort(e.target.value as SortByOptions)}
            sx={{ ml: 2, mr: 5, borderRadius: 1, flexGrow: 0, minWidth: 120, width: '10%' }}
          >
            <MenuItem value={"hottest"}>Hot</MenuItem>
            <MenuItem value={"date_added"}>Newest Creation</MenuItem>
            <MenuItem value={"date_modified"}>Newest Edit</MenuItem>
          </Select>
        )}
        {!isMobile && (
          <IconButton
            color="inherit"
            aria-label="Open in GitHub"
            href="https://github.com/h4ks-com/vibegames"
            target="_blank"
            rel="noopener noreferrer"
          >
            <GitHubIcon />
          </IconButton>
        )}
      </Toolbar>
    </AppBar>
  )
};
