import React from 'react';
import {Drawer, Container, Typography, TextField, List, ListItem, ListItemText} from '@mui/material';
import {Game} from '../types/game';

function openGameInNewTab(game: Game) {
  window.open(`${process.env.REACT_APP_API_URL}/api/game/${game.project}`, '_blank');
}

type Props = {
  open: boolean;
  onClose: () => void;
  favorites: Game[];
  search: string;
  setSearch: (s: string) => void;
};

export const Sidebar: React.FC<Props> = ({open, onClose, favorites, search, setSearch}) => {
  const filtered = favorites.filter((g) =>
    g.project.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <Drawer anchor="left" open={open} onClose={onClose}>
      <Container sx={{width: 300, p: 2}}>
        <Typography variant="h6">Favorite Games</Typography>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search favorites..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{my: 2}}
        />
        <List>
          {filtered.map((fav) => (
            <ListItem
              key={fav.project}
              onClick={
                () => openGameInNewTab(fav)
              }
              sx={{cursor: 'pointer'}}
            >
              <ListItemText primary={fav.project} />
            </ListItem>
          ))}
        </List>
      </Container>
    </Drawer>
  );
};
