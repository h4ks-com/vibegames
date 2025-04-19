import { CircularProgress } from '@mui/material';
import React, { useState } from 'react';
import BrokenImageIcon from '@mui/icons-material/BrokenImage';
import { useInView } from 'react-intersection-observer';

type Props = {
  thumbUrl: string;
};

export const GameThumbnail: React.FC<Props> = ({ thumbUrl }) => {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);
  const { ref, inView } = useInView({ triggerOnce: false });

  if (error) {
    return (
      <div
        ref={ref}
        style={{
          width: '100%',
          height: 200,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginTop: 8,
        }}
      >
        <BrokenImageIcon color="error" sx={{ fontSize: 64 }} />
      </div>
    );
  }

  return (
    <div ref={ref} style={{ width: '100%', height: 200, marginTop: 8 }}>
      {(inView && !loaded) && (
        <div
          style={{
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <CircularProgress size={40} color="primary" />
        </div>
      )}
      {(inView || loaded) && (
        <img
          src={thumbUrl}
          onLoad={() => setLoaded(true)}
          onError={() => setError(true)}
          style={{
            display: loaded ? 'block' : 'none',
            width: '100%',
            height: '100%',
            border: 'none',
            pointerEvents: 'none',
            backgroundColor: '#fff',
            overflow: 'hidden',
          }}
          alt="Game thumbnail"
        />
      )}
    </div>
  );
};
