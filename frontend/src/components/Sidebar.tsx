import React from 'react';
import { Drawer, Container, Typography, TextField, List, ListItem, ListItemText, IconButton } from '@mui/material';
import { Game } from '../types/game';
import { ClearAdorment } from './ClearAdorment';
import DeleteIcon from '@mui/icons-material/Delete';

function openGameInNewTab(game: Game) {
  window.open(`${process.env.REACT_APP_API_URL}${game.html_path}`, '_blank');
}

type Props = {
  open: boolean;
  onClose: () => void;
  favorites: Game[];
  search: string;
  setSearch: (s: string) => void;
  onDeleteFavorite: (game: Game) => void;
};

export const Sidebar: React.FC<Props> = ({ open, onClose, favorites, search, setSearch, onDeleteFavorite }) => {
  const filtered = favorites.filter((g) =>
    g.project.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Drawer anchor="left" open={open} onClose={onClose}>
      <Container sx={{ width: 300, p: 2 }}>
        <Typography variant="h6">Favorite Games</Typography>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search favorites..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ my: 2 }}
          slotProps={{
            input: {
              endAdornment: search && (
                <ClearAdorment
                  onClick={() => setSearch('')}
                />
              ),
            },
          }}
        />
        <List>
          {filtered.map((fav) => (
            <ListItem
              key={fav.project}
              secondaryAction={
                <IconButton edge="end" onClick={(e) => {
                  e.stopPropagation();
                  onDeleteFavorite(fav);
                }}>
                  <DeleteIcon />
                </IconButton>
              }
              onClick={() => openGameInNewTab(fav)}
              sx={{
                cursor: 'pointer',
                transition: 'background-color 0.3s, transform 0.2s',
                '&:hover': {
                  backgroundColor: 'rgba(0, 0, 0, 0.04)',
                },
                '&:active': {
                  transform: 'scale(0.98)',
                },
              }}
            >
              <ListItemText primary={fav.project} />
            </ListItem>
          ))}
        </List>
      </Container>
    </Drawer>
  );
};
